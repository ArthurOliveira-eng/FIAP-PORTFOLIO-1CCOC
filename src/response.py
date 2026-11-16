"""Apresenta modelos de resposta versionados sem um modelo externo."""
from datetime import date
from src.config import DISCLAIMER, LIMITATION, PROMPT_PATHS, STALE_AFTER_DAYS


class TemplateError(ValueError):
    """O modelo de resposta está indisponível ou malformado."""


def load_template(name):
    if name not in PROMPT_PATHS:
        raise TemplateError(f"Modelo de resposta desconhecido: {name}")
    try:
        text = PROMPT_PATHS[name].read_text(encoding="utf-8")
    except OSError as exc:
        raise TemplateError(f"Não foi possível ler o modelo de resposta: {exc}") from exc
    if text.count("---RESPONSE---") != 1:
        raise TemplateError("O modelo deve conter exatamente um delimitador de resposta.")
    return text.split("---RESPONSE---", 1)[1].strip()


def list_records(records):
    return "\n".join(f"  {record['id']} - {record['question']}" for record in records)


def generate_response(result, memory, template_name, *, today=None):
    """Exige fonte nas orientações e informa quando nenhuma fonte foi consultada."""
    if result.status == "match":
        record = result.records[0]
        related = list_records(memory.related(record["id"])) or "  Escolha outro tema."
        age = ((today or date.today()) - date.fromisoformat(record["verification_date"])).days
        stale = (
            "Aviso de atualização: este registro tem mais de 180 dias; consulte a fonte antes de agir."
            if age > STALE_AFTER_DAYS else ""
        )
        values = {
            **record, "related": related, "stale_warning": stale,
            "limitation": LIMITATION, "disclaimer": DISCLAIMER,
        }
        try:
            return load_template(template_name).format_map(values)
        except (KeyError, ValueError) as exc:
            raise TemplateError(f"Campos de substituição inválidos na resposta: {exc}") from exc
    if result.status in ("browse", "related", "ambiguous"):
        preface = result.message or "Escolha um ID de registro ou faça uma pergunta mais específica."
        return (
            f"{preface}\n{list_records(result.records)}\n"
            "Fonte: nenhuma fonte de orientação consultada ainda; selecione um registro para consultar sua fonte.\n"
            f"{DISCLAIMER}"
        )
    if result.status == "quit":
        return "Sessão encerrada. Confirme as orientações atuais nos canais oficiais."
    themes = "\n".join(f"  {index}. {theme}" for index, theme in enumerate(memory.themes, 1))
    return (
        f"{result.message}\n"
        "Fonte: nenhuma consultada; nenhuma orientação foi gerada.\n"
        f"Temas disponíveis:\n{themes}\n"
        "Experimente: 'Como recuperar minha senha do gov.br?' ou 'Onde buscar atendimento do CRAS?'\n"
        f"Limitação: {LIMITATION}\n{DISCLAIMER}"
    )
