"""Perception -> reasoning -> action, with file-backed memory and safe telemetry."""
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
            raise TemplateError(f"Unknown response template: {template}")
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
            return SearchResult("invalid_input", message="Enter text or a menu number.")
        query = raw_input.strip()
        command = normalize(query)
        if len(query) > MAX_QUERY_LENGTH:
            return SearchResult("invalid_input", message=f"Use at most {MAX_QUERY_LENGTH} characters.")
        if command in ("quit", "exit", "0"):
            return SearchResult("quit")
        if command in ("back", "help", "themes", "menu"):
            self.current_theme = None
            return SearchResult("menu", message="Choose a theme number or ask a question.")
        if command == "related":
            if self.last_record is None:
                return SearchResult("invalid_option", message="Consult a record before requesting related subjects.")
            return SearchResult("related", tuple(self.memory.related(self.last_record)), message="Choose a related record ID.")
        # Decimal strings are menu input, never interpreted as personal identifiers.
        if re.fullmatch(r"[+-]?\d+", query):
            if query.isascii() and query.isdigit() and 1 <= int(query) <= len(self.memory.themes):
                self.current_theme = self.memory.themes[int(query) - 1]
                return search(self.memory, theme=self.current_theme)
            return SearchResult("invalid_option", message="Invalid menu option. Choose an available theme number.")
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
        # Only a controlled vocabulary is retained. No raw queries, hashes,
        # names, e-mails, document numbers, or credentials are written to disk.
        query = raw_input if isinstance(raw_input, str) else ""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": {"length": len(query), "known_terms": sorted(tokens(query) & self.vocabulary)},
            "status": result.status, "matched_records": list(record_ids),
            "template": self.template, "theme": self.current_theme,
            "latency_ms": round(latency_ms, 6),
        }
        log_error = None
        if self.log_path is not None:
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with self.log_path.open("a", encoding="utf-8") as output:
                    output.write(json.dumps(event, ensure_ascii=False) + "\n")
            except OSError as exc:
                log_error = f"Telemetry could not be saved ({type(exc).__name__}); guidance remains available."
        return Answer(result.status, record_ids, text, latency_ms, self.current_theme, log_error)
