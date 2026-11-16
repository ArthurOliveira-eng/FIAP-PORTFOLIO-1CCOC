"""Render versioned prompt/response templates without an external model."""
from datetime import date
from src.config import DISCLAIMER, LIMITATION, PROMPT_PATHS, STALE_AFTER_DAYS


class TemplateError(ValueError):
    """A selected template is unavailable or malformed."""


def load_template(name):
    if name not in PROMPT_PATHS:
        raise TemplateError(f"Unknown response template: {name}")
    try:
        text = PROMPT_PATHS[name].read_text(encoding="utf-8")
    except OSError as exc:
        raise TemplateError(f"Cannot read response template: {exc}") from exc
    if text.count("---RESPONSE---") != 1:
        raise TemplateError("The response template must contain one response delimiter.")
    return text.split("---RESPONSE---", 1)[1].strip()


def list_records(records):
    return "\n".join(f"  {record['id']} - {record['question']}" for record in records)


def generate_response(result, memory, template_name, *, today=None):
    """A source is mandatory for guidance; fallbacks explicitly report none consulted."""
    if result.status == "match":
        record = result.records[0]
        related = list_records(memory.related(record["id"])) or "  Choose another theme."
        age = ((today or date.today()) - date.fromisoformat(record["verification_date"])).days
        stale = (
            "Freshness warning: this record is over 180 days old; recheck the source before acting."
            if age > STALE_AFTER_DAYS else ""
        )
        values = {
            **record, "related": related, "stale_warning": stale,
            "limitation": LIMITATION, "disclaimer": DISCLAIMER,
        }
        try:
            return load_template(template_name).format_map(values)
        except (KeyError, ValueError) as exc:
            raise TemplateError(f"Invalid response placeholders: {exc}") from exc
    if result.status in ("browse", "related", "ambiguous"):
        preface = result.message or "Choose a record ID, or ask a more specific question."
        return (
            f"{preface}\n{list_records(result.records)}\n"
            "Source: no guidance source consulted yet; select a record for its source.\n"
            f"{DISCLAIMER}"
        )
    if result.status == "quit":
        return "Session ended. Confirm current guidance through official channels."
    themes = "\n".join(f"  {index}. {theme}" for index, theme in enumerate(memory.themes, 1))
    return (
        f"{result.message}\n"
        "Source: none consulted; no guidance has been generated.\n"
        f"Available themes:\n{themes}\n"
        "Try: 'How do I recover my gov.br password?' or 'Where can I access CRAS support?'\n"
        f"Limitation: {LIMITATION}\n{DISCLAIMER}"
    )
