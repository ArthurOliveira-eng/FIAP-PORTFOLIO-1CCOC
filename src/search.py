"""Deterministic lexical retrieval with conservative ambiguity handling."""
import re
import unicodedata
from dataclasses import dataclass
from src.config import AMBIGUITY_MARGIN, MIN_SCORE

STOP_WORDS = set(
    "a an the is are was were be to of for on in at by and or i my me we our "
    "you your can could would should how what where when which do does did "
    "please need want get find use about with have has it this that help "
    "before after there from as".split()
)
SYNONYMS = {
    "forgot": "recover", "forgotten": "recover", "lost": "recover",
    "reset": "recover", "passwords": "password",
    "register": "registration", "enroll": "registration", "apply": "registration",
    "registering": "registration", "enrollment": "registration",
    "creating": "create", "open": "create",
    "renew": "update", "updating": "update", "changed": "update",
    "address": "residence", "moved": "update",
    "check": "consult", "checking": "consult",
    "levels": "level", "upgrade": "increase", "upgrading": "increase",
    "signing": "sign", "signature": "sign",
    "papers": "evidence", "receipts": "evidence", "proof": "evidence",
    "documents": "document", "complaints": "complaint",
    "taxpayer": "cpf", "identification": "identity",
}
# These instructions ask for behavior outside the retrieval agent's role.
INSTRUCTION_OVERRIDE = re.compile(
    r"\b(ignore|override|disregard)\b.{0,50}\b(instructions|rules|sources)\b"
    r"|\b(system prompt|reveal secrets|invent an answer|pretend to be official)\b",
    re.IGNORECASE,
)


def normalize(text):
    folded = unicodedata.normalize("NFKD", text.casefold())
    return " ".join(re.findall(r"[a-z0-9]+", "".join(
        char for char in folded if not unicodedata.combining(char)
    )))


def tokens(text):
    return {SYNONYMS.get(word, word) for word in normalize(text).split() if word not in STOP_WORDS}


def score_record(record, query_tokens):
    """Combine query coverage with a bonus for a complete keyword phrase."""
    aliases = [tokens(keyword) for keyword in record["keywords"]]
    document_tokens = tokens(record["question"]) | set().union(*aliases)
    coverage = len(query_tokens & document_tokens) / len(query_tokens)
    # A broad single word does not earn the phrase bonus.
    phrase_bonus = 0.20 if any(
        len(alias) >= 2 and alias <= query_tokens for alias in aliases
    ) else 0.0
    return coverage + phrase_bonus


@dataclass(frozen=True)
class SearchResult:
    status: str
    records: tuple = ()
    scores: tuple = ()
    message: str = ""


def search(memory, question="", theme=None):
    """Retrieve by ID, theme, or lexical evidence; never synthesize missing facts."""
    if theme is not None and theme not in memory.by_theme:
        return SearchResult("invalid_option", message="Choose one of the available themes.")
    question = question.strip()
    if not question:
        if theme is not None:
            return SearchResult("browse", tuple(memory.by_theme[theme]))
        return SearchResult("empty", message="Enter a question or choose a theme number.")
    if question.upper() in memory.by_id:
        return SearchResult("match", (memory.by_id[question.upper()],), (1.0,))
    if INSTRUCTION_OVERRIDE.search(question):
        return SearchResult("no_match", message="I can only return stored guidance with its source.")
    query_tokens = tokens(question)
    if not query_tokens:
        return SearchResult("empty", message="Enter a question containing words, or choose a theme.")
    records = memory.by_theme[theme] if theme else memory.records
    ranked = []
    for record in records:
        score = score_record(record, query_tokens)
        if score >= MIN_SCORE:
            ranked.append((score, record["id"], record))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    if not ranked:
        return SearchResult("no_match", message="No reliable answer to that question is stored in the base.")
    best = ranked[0][0]
    close = [item for item in ranked if best - item[0] <= AMBIGUITY_MARGIN]
    # A one-word topic has too little intent information, even with one candidate.
    if len(query_tokens) == 1 or len(close) > 1:
        return SearchResult(
            "ambiguous", tuple(item[2] for item in close[:5]),
            tuple(round(item[0], 4) for item in close[:5]),
            "That query may refer to different subjects. Choose a record ID or add details.",
        )
    return SearchResult("match", (ranked[0][2],), (round(best, 4),))
