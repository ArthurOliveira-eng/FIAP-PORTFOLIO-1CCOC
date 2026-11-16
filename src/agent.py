"""Percepção, raciocínio e ação com memória em arquivo e telemetria segura."""
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from src.config import DEFAULT_TEMPLATE, LOG_PATH, MAX_QUERY_LENGTH, PROMPT_PATHS
from src.response import TemplateError, generate_response
from src.search import SearchResult, normalize, search, tokens


@dataclass(frozen=True)
class Answer:
    status: str
    record_ids: tuple
    text: str
    latency_ms: float
    theme: str | None
    log_error: str | None = None


class CitizenAgent:
    def __init__(self, memory, *, template=DEFAULT_TEMPLATE, log_path=LOG_PATH):
        if template not in PROMPT_PATHS:
            raise TemplateError(f"Modelo de resposta desconhecido: {template}")
        self.memory = memory
        self.template = template
        self.log_path = Path(log_path) if log_path is not None else None
        self.current_theme = None
        self.last_record = None
        self.vocabulary = set().union(*(
            tokens(" ".join(record["keywords"])) for record in memory.records
        ))

    def perceive(self, raw_input):
        if not isinstance(raw_input, str):
            return SearchResult("invalid_input", message="Digite um texto ou número do menu.")
        query = raw_input.strip()
        command = normalize(query)
        if len(query) > MAX_QUERY_LENGTH:
            return SearchResult("invalid_input", message=f"Use no máximo {MAX_QUERY_LENGTH} caracteres.")
        if command in ("sair", "encerrar", "0", "quit", "exit"):
            return SearchResult("quit")
        if command in ("voltar", "ajuda", "temas", "menu", "back", "help", "themes"):
            self.current_theme = None
            return SearchResult("menu", message="Escolha o número de um tema ou faça uma pergunta.")
        if command in ("relacionados", "related"):
            if self.last_record is None:
                return SearchResult("invalid_option", message="Consulte um registro antes de pedir assuntos relacionados.")
            return SearchResult("related", tuple(self.memory.related(self.last_record)), message="Escolha o ID de um registro relacionado.")
        # Números são opções do menu, nunca identificadores pessoais.
        if re.fullmatch(r"[+-]?\d+", query):
            if query.isascii() and query.isdigit() and 1 <= int(query) <= len(self.memory.themes):
                self.current_theme = self.memory.themes[int(query) - 1]
                return search(self.memory, theme=self.current_theme)
            return SearchResult("invalid_option", message="Opção de menu inválida. Escolha o número de um tema disponível.")
        selected = next(
            (theme for theme in self.memory.themes if normalize(theme) == command), None
        )
        if selected:
            self.current_theme = selected
            return search(self.memory, theme=selected)
        return search(self.memory, query, self.current_theme)

    def handle(self, raw_input):
        started = perf_counter()
        result = self.perceive(raw_input)
        if result.status == "match":
            self.last_record = result.records[0]["id"]
        text = generate_response(result, self.memory, self.template)
        latency_ms = (perf_counter() - started) * 1000
        record_ids = tuple(record["id"] for record in result.records)
        log_error = self._write_log(raw_input, result.status, record_ids, latency_ms)
        return Answer(result.status, record_ids, text, latency_ms, self.current_theme, log_error)

    def _write_log(self, raw_input, status, record_ids, latency_ms):
        """Salva metadados operacionais sem persistir a consulta original."""
        if self.log_path is None:
            return None
        query = raw_input if isinstance(raw_input, str) else ""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": {"length": len(query), "known_terms": sorted(tokens(query) & self.vocabulary)},
            "status": status, "matched_records": list(record_ids),
            "template": self.template, "theme": self.current_theme,
            "latency_ms": round(latency_ms, 6),
        }
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as exc:
            return f"Não foi possível salvar a telemetria ({type(exc).__name__}); a orientação continua disponível."
        return None
