"""Load, validate, index, and safely maintain the file-backed memory."""
import json
import os
import re
import tempfile
from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


class KnowledgeBaseError(ValueError):
    """A file cannot safely serve as the agent's knowledge memory."""


TEXT_FIELDS = (
    "id", "theme", "question", "summary_guidance", "reference",
    "verification_date", "confirmation_warning",
)


def validate_records(records):
    """Reject the whole snapshot if any essential record or graph edge is invalid."""
    if not isinstance(records, list) or not records:
        raise KnowledgeBaseError("The knowledge base must be a non-empty JSON list.")
    ids = set()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise KnowledgeBaseError(f"Record {index} must be an object.")
        for field in TEXT_FIELDS:
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise KnowledgeBaseError(f"Record {index}: missing or invalid {field}.")
        identifier = record["id"]
        if not re.fullmatch(r"[A-Z][0-9]{2,}", identifier) or identifier in ids:
            raise KnowledgeBaseError(f"Record {index}: invalid or duplicate ID.")
        ids.add(identifier)
        for field in ("keywords", "related_ids"):
            value = record.get(field)
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise KnowledgeBaseError(f"{identifier}: {field} must be a list of strings.")
            if field == "keywords" and not value:
                raise KnowledgeBaseError(f"{identifier}: keywords cannot be empty.")
            if len(value) != len(set(value)):
                raise KnowledgeBaseError(f"{identifier}: duplicate {field} entries.")
        try:
            source = urlparse(record["reference"])
            port = source.port
        except ValueError as exc:
            raise KnowledgeBaseError(f"{identifier}: malformed source URL.") from exc
        if (
            source.scheme != "https" or not source.hostname
            or not (source.hostname == "gov.br" or source.hostname.endswith(".gov.br"))
            or source.username or source.password or port not in (None, 443)
        ):
            raise KnowledgeBaseError(f"{identifier}: expected an HTTPS Brazilian government source.")
        try:
            verified = date.fromisoformat(record["verification_date"])
        except ValueError as exc:
            raise KnowledgeBaseError(f"{identifier}: verification_date must be ISO YYYY-MM-DD.") from exc
        if verified.isoformat() != record["verification_date"] or verified > date.today():
            raise KnowledgeBaseError(f"{identifier}: invalid or future verification date.")
    for record in records:
        if any(target not in ids or target == record["id"] for target in record["related_ids"]):
            raise KnowledgeBaseError(f"{record['id']}: dangling or self-referencing related ID.")
    return records


class KnowledgeBase:
    """Lists preserve display order; dictionaries provide ID and theme indexes."""

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
                raise KnowledgeBaseError("The knowledge file is empty.")
            return cls(json.loads(text))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise KnowledgeBaseError(f"Cannot load knowledge base: {exc}") from exc

    def related(self, identifier):
        return [self.by_id[target] for target in self.graph.get(identifier, [])]


def save_record(path, record, *, replace=False):
    """Add/correct a complete record after validating the entire resulting graph.

    The old file remains intact on validation failure. Replacements use an atomic
    rename on the same filesystem. Administrative use only, outside the citizen UI.
    """
    path = Path(path)
    memory = KnowledgeBase.load(path)
    exists = record.get("id") in memory.by_id if isinstance(record, dict) else False
    if replace != exists:
        action = "already exists; use replace=True" if exists else "does not exist for replacement"
        raise KnowledgeBaseError(f"Record {action}.")
    records = [
        record if item["id"] == record.get("id") else item for item in memory.records
    ] if replace else memory.records + [record]
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
