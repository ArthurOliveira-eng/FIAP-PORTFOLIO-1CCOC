"""Carrega, valida, indexa e mantém a memória em arquivo com segurança."""
import json
import os
import re
import tempfile
from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


class KnowledgeBaseError(ValueError):
    """O arquivo não pode ser usado com segurança como memória de conhecimento."""


TEXT_FIELDS = (
    "id", "theme", "question", "summary_guidance", "reference",
    "verification_date", "confirmation_warning",
)


def validate_records(records):
    """Rejeita toda a base se algum registro essencial ou ligação for inválido."""
    if not isinstance(records, list) or not records:
        raise KnowledgeBaseError("A base de conhecimento deve ser uma lista JSON não vazia.")
    ids = set()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise KnowledgeBaseError(f"O registro {index} deve ser um objeto.")
        for field in TEXT_FIELDS:
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise KnowledgeBaseError(f"Registro {index}: campo {field} ausente ou inválido.")
        identifier = record["id"]
        if not re.fullmatch(r"[A-Z][0-9]{2,}", identifier) or identifier in ids:
            raise KnowledgeBaseError(f"Registro {index}: ID inválido ou duplicado.")
        ids.add(identifier)
        for field in ("keywords", "related_ids"):
            value = record.get(field)
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise KnowledgeBaseError(f"{identifier}: {field} deve ser uma lista de textos.")
            if field == "keywords" and not value:
                raise KnowledgeBaseError(f"{identifier}: a lista de palavras-chave não pode estar vazia.")
            if len(value) != len(set(value)):
                raise KnowledgeBaseError(f"{identifier}: valores duplicados em {field}.")
        try:
            source = urlparse(record["reference"])
            port = source.port
        except ValueError as exc:
            raise KnowledgeBaseError(f"{identifier}: URL da fonte malformada.") from exc
        if (
            source.scheme != "https" or not source.hostname
            or not (source.hostname == "gov.br" or source.hostname.endswith(".gov.br"))
            or source.username or source.password or port not in (None, 443)
        ):
            raise KnowledgeBaseError(f"{identifier}: a fonte deve ser uma página do governo brasileiro com HTTPS.")
        try:
            verified = date.fromisoformat(record["verification_date"])
        except ValueError as exc:
            raise KnowledgeBaseError(f"{identifier}: verification_date deve seguir o formato ISO AAAA-MM-DD.") from exc
        if verified.isoformat() != record["verification_date"] or verified > date.today():
            raise KnowledgeBaseError(f"{identifier}: data de verificação inválida ou futura.")
    for record in records:
        if any(target not in ids or target == record["id"] for target in record["related_ids"]):
            raise KnowledgeBaseError(f"{record['id']}: ID relacionado inexistente ou igual ao próprio registro.")
    return records


class KnowledgeBase:
    """Listas preservam a ordem; dicionários fornecem índices por ID e tema."""

    def __init__(self, records):
        self.records = deepcopy(validate_records(records))
        self.by_id = {record["id"]: record for record in self.records}
        self.by_theme = {}
        for record in self.records:
            self.by_theme.setdefault(record["theme"], []).append(record)
        self.themes = list(self.by_theme)
        self.graph = {record["id"]: list(record["related_ids"]) for record in self.records}

    @classmethod
    def load(cls, path):
        try:
            text = Path(path).read_text(encoding="utf-8")
            if not text.strip():
                raise KnowledgeBaseError("O arquivo de conhecimento está vazio.")
            return cls(json.loads(text))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise KnowledgeBaseError(f"Não foi possível carregar a base de conhecimento: {exc}") from exc

    def related(self, identifier):
        return [self.by_id[target] for target in self.graph.get(identifier, [])]


def save_record(path, record, *, replace=False):
    """Adiciona ou corrige um registro após validar todo o grafo resultante.

    O arquivo anterior é preservado se a validação falhar. A substituição é atômica
    no mesmo sistema de arquivos. Uso administrativo, fora da interface do cidadão.
    """
    path = Path(path)
    memory = KnowledgeBase.load(path)
    exists = record.get("id") in memory.by_id if isinstance(record, dict) else False
    if replace != exists:
        action = "já existe; use replace=True" if exists else "não existe para substituição"
        raise KnowledgeBaseError(f"O registro {action}.")
    if replace:
        records = [
            record if item["id"] == record["id"] else item
            for item in memory.records
        ]
    else:
        records = memory.records + [record]
    validate_records(records)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as output:
            temporary = Path(output.name)
            json.dump(records, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
