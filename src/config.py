"""Central configuration; no network calls or credentials are required."""
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
    "Independent educational prototype; not an official public agency channel. "
    "Do not enter personal data, passwords, or document numbers."
)
LIMITATION = (
    "This is a summary of the stored guidance, not a complete procedure or a "
    "personal eligibility decision. Confirm current requirements with the cited agency."
)
