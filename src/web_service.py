# SERVICO DE CONSULTAS WEB
import json
import threading
from datetime import date

from src.agent import CitizenAgent
from src.config import (
    DISCLAIMER,
    LIMITATION,
    MAX_QUERY_LENGTH,
    PROMPT_PATHS,
    ROOT,
    STALE_AFTER_DAYS,
)

RESULTADOS = ROOT / "tests" / "results.json"
USABILIDADE = ROOT / "tests" / "usability_results.json"
MAX_SESSOES = 50


def registro(r):
    dias = (date.today() - date.fromisoformat(r["verification_date"])).days
    return {
        "id": r["id"],
        "tema": r["theme"],
        "pergunta": r["question"],
        "resumo": r["summary_guidance"],
        "fonte": r["reference"],
        "data": r["verification_date"],
        "aviso": r["confirmation_warning"],
        "defasado": dias > STALE_AFTER_DAYS,
    }


def ler_json(caminho):
    try:
        resultado = json.loads(caminho.read_text(encoding="utf-8"))
        return resultado if isinstance(resultado, dict) else None
    except (OSError, ValueError, UnicodeError):
        return None


class Servico:
    """Uma instância de CitizenAgent por sessão do navegador (guarda tema atual e último registro)."""

    def __init__(self, memoria, modelo, log):
        self.memoria, self.modelo, self.log = memoria, modelo, log
        self.agentes, self.trava = {}, threading.Lock()

    def estado(self):
        return {
            "temas": [
                {"nome": t, "total": len(self.memoria.by_theme[t])}
                for t in self.memoria.themes
            ],
            "modelos": list(PROMPT_PATHS),
            "modelo": self.modelo,
            "log": self.log is not None,
            "max": MAX_QUERY_LENGTH,
            "total": len(self.memoria.records),
            "dias": STALE_AFTER_DAYS,
            "limitacao": LIMITATION,
            "aviso": DISCLAIMER,
        }

    def base(self):
        return [registro(item) for item in self.memoria.records]

    def indicadores(self):
        av, us = ler_json(RESULTADOS), ler_json(USABILIDADE)
        if av:
            av = {
                k: av.get(k)
                for k in (
                    "executed_at",
                    "environment",
                    "python_version",
                    "methodology",
                    "metrics_by_template",
                    "metrics_by_category",
                )
            }
        if us:
            tarefas = us.get("tasks", [])
            us = {
                k: us.get(k)
                for k in (
                    "executed_at",
                    "study_type",
                    "human_participants",
                    "task_completion_rate",
                    "average_script_actions",
                    "average_process_time_ms",
                    "limitations",
                )
            }
            us["tasks"] = [
                {
                    "id": t.get("id"),
                    "task": t.get("task"),
                    "difficulty": t.get("difficulty"),
                }
                for t in tarefas
            ]
        return {"avaliacao": av, "usabilidade": us}

    def consultar(self, sid, texto, modelo, tema=None, reiniciar=False):
        with self.trava:
            if modelo and modelo not in PROMPT_PATHS:
                raise ValueError("Modelo inválido")
            if tema is not None and tema not in ("", *self.memoria.themes):
                raise ValueError("Tema inválido")
            if reiniciar:
                self.agentes.pop(sid, None)
            agente = self.agentes.get(sid)
            if agente is None:
                if len(self.agentes) >= MAX_SESSOES:
                    self.agentes.pop(next(iter(self.agentes)))
                agente = self.agentes[sid] = CitizenAgent(
                    self.memoria, template=self.modelo, log_path=self.log
                )
            if modelo in PROMPT_PATHS:
                agente.template = modelo
            if tema is not None:
                agente.current_theme = tema or None
            resp = agente.handle(texto)
        ids = list(resp.record_ids)
        relacionados = []
        if resp.status == "match":
            relacionados = [
                {"id": r["id"], "tema": r["theme"], "pergunta": r["question"]}
                for r in self.memoria.related(ids[0])
            ]
        return {
            "status": resp.status,
            "ids": ids,
            "texto": resp.text,
            "mensagem": resp.text.splitlines()[0] if resp.text else "",
            "latencia_ms": round(resp.latency_ms, 3),
            "tema": resp.theme,
            "log_erro": resp.log_error,
            "registros": [registro(self.memoria.by_id[i]) for i in ids],
            "relacionados": relacionados,
        }
