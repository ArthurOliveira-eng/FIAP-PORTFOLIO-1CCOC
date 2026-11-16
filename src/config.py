"""Configuração central, sem chamadas de rede nem credenciais."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_PATH = ROOT / "data" / "knowledge_base.json"
QUESTIONS_PATH = ROOT / "tests" / "test_questions.json"
RESULTS_PATH = ROOT / "tests" / "results.json"
LOG_PATH = ROOT / "logs" / "queries.jsonl"
PROMPT_PATHS = {
    "template_a_v1": ROOT / "prompts" / "template_a.txt",
    "template_b_v1": ROOT / "prompts" / "template_b.txt",
}
DEFAULT_TEMPLATE = "template_b_v1"
MIN_SCORE = 0.46
AMBIGUITY_MARGIN = 0.12
MAX_QUERY_LENGTH = 500
STALE_AFTER_DAYS = 180
DISCLAIMER = (
    "Protótipo educacional independente; não é um canal oficial de órgão público. "
    "Não informe dados pessoais, senhas ou números de documentos."
)
LIMITATION = (
    "Este é um resumo da orientação armazenada, não um procedimento completo nem uma "
    "decisão individual de elegibilidade. Confirme os requisitos atuais com o órgão citado."
)
