"""Busca lexical determinística com tratamento conservador de ambiguidades."""

import re
import unicodedata
from dataclasses import dataclass
from src.config import AMBIGUITY_MARGIN, MIN_SCORE

STOP_WORDS = set(
    "a o as os um uma uns umas de da do das dos em no na nos nas para por "
    "e ou eu meu minha meus minhas voce seu sua seus suas como qual quais "
    "que oque onde quando posso pode poderia devo preciso quero fazer "
    "ter tenho tem se ser sao e esta estou ao aos pela pelo pelas pelos "
    "com sem sobre isso isto esse essa antes depois por favor me uma".split()
)
SYNONYMS = {
    "esqueci": "recuperar",
    "esquecida": "recuperar",
    "perdi": "recuperar",
    "redefinir": "recuperar",
    "recuperacao": "recuperar",
    "senhas": "senha",
    "cadastrar": "inscricao",
    "inscrever": "inscricao",
    "cadastro": "inscricao",
    "criacao": "criar",
    "abrir": "criar",
    "renovar": "atualizar",
    "atualizacao": "atualizar",
    "mudei": "atualizar",
    "endereco": "residencia",
    "verificar": "consultar",
    "conferir": "consultar",
    "consulta": "consultar",
    "niveis": "nivel",
    "elevar": "aumentar",
    "assinatura": "assinar",
    "eletronica": "eletronicamente",
    "comprovantes": "comprovante",
    "provas": "comprovante",
    "documentos": "documento",
    "reclamacoes": "reclamacao",
    "identificacao": "identidade",
    "cadunico": "unico",
    "atendimento": "atender",
    "apoio": "atender",
    "ajuda": "atender",
}
# Estas instruções tentam alterar o papel do agente de busca.
INSTRUCTION_OVERRIDE = re.compile(
    r"\b(ignore|desconsidere|sobrescreva|override|disregard)\b.{0,50}"
    r"\b(instrucoes|regras|fontes|instructions|rules|sources)\b"
    r"|\b(invente uma resposta|revele segredos|finja ser oficial|prompt do sistema|"
    r"system prompt|reveal secrets|invent an answer|pretend to be official)\b",
    re.IGNORECASE,
)


def normalize(text):
    folded = unicodedata.normalize("NFKD", text.casefold())
    return " ".join(
        re.findall(
            r"[a-z0-9]+",
            "".join(char for char in folded if not unicodedata.combining(char)),
        )
    )


def tokens(text):
    return {
        SYNONYMS.get(word, word)
        for word in normalize(text).split()
        if word not in STOP_WORDS
    }


def build_index(records):
    """Normaliza os registros uma vez durante o carregamento da base."""
    index = {}
    for record in records:
        aliases = [tokens(keyword) for keyword in record["keywords"]]
        index[record["id"]] = {
            "terms": tokens(record["question"]) | set().union(*aliases),
            "aliases": aliases,
        }
    return index


def score_record(indexed_record, query_tokens):
    """Combina cobertura dos termos e bônus por expressão completa."""
    aliases = indexed_record["aliases"]
    document_tokens = indexed_record["terms"]
    coverage = len(query_tokens & document_tokens) / len(query_tokens)
    # Uma palavra isolada não recebe o bônus de expressão.
    phrase_bonus = (
        0.20
        if any(len(alias) >= 2 and alias <= query_tokens for alias in aliases)
        else 0.0
    )
    return coverage + phrase_bonus


@dataclass(frozen=True)
class SearchResult:
    status: str
    records: tuple = ()
    scores: tuple = ()
    message: str = ""


def search(memory, question="", theme=None):
    """Busca por ID, tema ou termos, sem inventar fatos ausentes."""
    if theme is not None and theme not in memory.by_theme:
        return SearchResult(
            "invalid_option", message="Escolha um dos temas disponíveis."
        )
    question = question.strip()
    if not question:
        if theme is not None:
            return SearchResult("browse", tuple(memory.by_theme[theme]))
        return SearchResult(
            "empty", message="Digite uma pergunta ou escolha o número de um tema."
        )
    if question.upper() in memory.by_id:
        return SearchResult("match", (memory.by_id[question.upper()],), (1.0,))
    if INSTRUCTION_OVERRIDE.search(normalize(question)):
        return SearchResult(
            "no_match",
            message="Posso retornar apenas orientações armazenadas com sua fonte.",
        )
    query_tokens = tokens(question)
    if not query_tokens:
        return SearchResult(
            "empty", message="Digite uma pergunta contendo palavras ou escolha um tema."
        )
    records = memory.by_theme[theme] if theme else memory.records
    ranked = []
    for record in records:
        score = score_record(memory.search_index[record["id"]], query_tokens)
        if score >= MIN_SCORE:
            ranked.append((score, record["id"], record))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    if not ranked:
        return SearchResult(
            "no_match", message="Não há resposta confiável para essa pergunta na base."
        )
    best = ranked[0][0]
    close = [item for item in ranked if best - item[0] <= AMBIGUITY_MARGIN]
    # Uma palavra isolada não esclarece a intenção, mesmo com um único candidato.
    if len(query_tokens) == 1 or len(close) > 1:
        return SearchResult(
            "ambiguous",
            tuple(item[2] for item in close[:5]),
            tuple(round(item[0], 4) for item in close[:5]),
            "Essa consulta pode se referir a assuntos diferentes. Escolha um ID de registro ou acrescente detalhes.",
        )
    return SearchResult("match", (ranked[0][2],), (round(best, 4),))
