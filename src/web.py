"""Interface web OPCIONAL do Citizen Assist AI (somente biblioteca padrão).

O terminal continua sendo a interface principal:  python src/sistema.py
Esta camada extra reutiliza o MESMO agente, a MESMA base e os MESMOS modelos de resposta:

    python src/web.py                 -> http://127.0.0.1:8000
    python src/web.py --modelo template_a_v1 --sem-log --porta 8080

Nada de busca duplicada: cada consulta passa por CitizenAgent.handle, exatamente como no CLI.
O servidor escuta só em 127.0.0.1, não faz chamadas externas e não imprime as consultas.
"""
import json
import re
import sys
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import CitizenAgent
from src.cli import ArgumentParser
from src.config import (DEFAULT_TEMPLATE, DISCLAIMER, KNOWLEDGE_PATH, LIMITATION, LOG_PATH,
                        MAX_QUERY_LENGTH, PROMPT_PATHS, ROOT, STALE_AFTER_DAYS)
from src.knowledge_base import KnowledgeBase, KnowledgeBaseError
from src.response import TemplateError

HTML = ROOT / "web" / "index.html"
RESULTADOS = ROOT / "tests" / "results.json"
USABILIDADE = ROOT / "tests" / "usability_results.json"
SESSAO = re.compile(r"[A-Za-z0-9]{8,40}")


def registro(r):
    dias = (date.today() - date.fromisoformat(r["verification_date"])).days
    return {"id": r["id"], "tema": r["theme"], "pergunta": r["question"], "resumo": r["summary_guidance"],
            "fonte": r["reference"], "data": r["verification_date"], "aviso": r["confirmation_warning"],
            "defasado": dias > STALE_AFTER_DAYS}


def ler_json(caminho):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class Servico:
    """Uma instância de CitizenAgent por sessão do navegador (guarda tema atual e último registro)."""

    def __init__(self, memoria, modelo, log):
        self.memoria, self.modelo, self.log = memoria, modelo, log
        self.agentes, self.trava = {}, threading.Lock()

    def estado(self):
        return {"temas": [{"nome": t, "total": len(self.memoria.by_theme[t])} for t in self.memoria.themes],
                "modelos": list(PROMPT_PATHS), "modelo": self.modelo, "log": self.log is not None,
                "max": MAX_QUERY_LENGTH, "total": len(self.memoria.records), "dias": STALE_AFTER_DAYS,
                "limitacao": LIMITATION, "aviso": DISCLAIMER}

    def indicadores(self):
        av, us = ler_json(RESULTADOS), ler_json(USABILIDADE)
        if av:
            av = {k: av.get(k) for k in ("executed_at", "environment", "python_version", "methodology",
                                         "metrics_by_template", "metrics_by_category")}
        if us:
            us = {k: us.get(k) for k in ("executed_at", "study_type", "human_participants", "task_completion_rate",
                                         "average_script_actions", "average_process_time_ms", "limitations")}
            us["tasks"] = [{"id": t.get("id"), "task": t.get("task"), "difficulty": t.get("difficulty")}
                           for t in (ler_json(USABILIDADE) or {}).get("tasks", [])]
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
                if len(self.agentes) >= 50:
                    self.agentes.pop(next(iter(self.agentes)))
                agente = self.agentes[sid] = CitizenAgent(self.memoria, template=self.modelo, log_path=self.log)
            if modelo in PROMPT_PATHS:
                agente.template = modelo
            if tema is not None:
                agente.current_theme = tema or None
            resp = agente.handle(texto)
        ids = list(resp.record_ids)
        relacionados = []
        if resp.status == "match":
            relacionados = [{"id": r["id"], "tema": r["theme"], "pergunta": r["question"]}
                            for r in self.memoria.related(ids[0])]
        return {"status": resp.status, "ids": ids, "texto": resp.text,
                "mensagem": resp.text.splitlines()[0] if resp.text else "",
                "latencia_ms": round(resp.latency_ms, 3), "tema": resp.theme, "log_erro": resp.log_error,
                "registros": [registro(self.memoria.by_id[i]) for i in ids], "relacionados": relacionados}


def criar_manipulador(servico):
    class Manipulador(BaseHTTPRequestHandler):
        def enviar(self, codigo, corpo, tipo="application/json; charset=utf-8"):
            dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(dados)

        def do_GET(self):
            arquivos = {
                "/app.js": (ROOT / "web/app.js", "text/javascript; charset=utf-8"),
                "/style.css": (ROOT / "web/style.css", "text/css; charset=utf-8"),
                "/inter.woff2": (ROOT / "web/inter.woff2", "font/woff2"),
            }
            if self.path in arquivos:
                caminho, tipo = arquivos[self.path]
                try:
                    return self.enviar(200, caminho.read_bytes(), tipo)
                except OSError:
                    return self.enviar(404, {"erro": "Recurso indisponível."})
            if self.path in ("/", "/index.html"):
                try:
                    self.enviar(200, HTML.read_bytes(), "text/html; charset=utf-8")
                except OSError:
                    self.enviar(404, {"erro": "web/index.html não encontrado"})
            elif self.path == "/api/estado":
                self.enviar(200, servico.estado())
            elif self.path == "/api/base":
                self.enviar(200, [registro(r) for r in servico.memoria.records])
            elif self.path == "/api/indicadores":
                self.enviar(200, servico.indicadores())
            else:
                self.enviar(404, {"erro": "não encontrado"})

        def do_POST(self):
            if self.path != "/api/consultar":
                return self.enviar(404, {"erro": "não encontrado"})
            try:
                tamanho = int(self.headers.get("Content-Length", 0))
                if not 0 < tamanho <= 8192:
                    return self.enviar(413, {"erro": "Pedido muito grande ou vazio."})
                pedido = json.loads(self.rfile.read(tamanho) or b"{}")
                if not isinstance(pedido, dict):
                    return self.enviar(400, {"erro": "Envie um objeto JSON."})
                sid = str(pedido.get("sid", ""))
                if not SESSAO.fullmatch(sid):
                    return self.enviar(400, {"erro": "sessão inválida"})
                texto = pedido.get("texto", "")
                self.enviar(200, servico.consultar(sid, texto if isinstance(texto, str) else None,
                                                   str(pedido.get("modelo", "")),
                                                   pedido.get("tema"), pedido.get("reiniciar") is True))
            except TemplateError as exc:
                self.enviar(500, {"status": "erro", "mensagem": str(exc), "registros": [], "relacionados": [],
                                  "texto": "", "latencia_ms": 0, "tema": None, "log_erro": None})
            except (ValueError, OSError):
                self.enviar(400, {"erro": "pedido inválido"})

        def log_message(self, *args):  # privacidade: sem registro de acessos nem de consultas
            pass

    return Manipulador


def main(argv=None):
    parser = ArgumentParser(description="Citizen Assist AI: interface web opcional e local.")
    parser.add_argument("--base", "--knowledge", dest="knowledge", type=Path, default=KNOWLEDGE_PATH,
                        metavar="ARQUIVO", help="Arquivo JSON da base de conhecimento.")
    parser.add_argument("--modelo", "--template", dest="template", choices=PROMPT_PATHS,
                        default=DEFAULT_TEMPLATE, help="Modelo de resposta inicial.")
    parser.add_argument("--sem-log", "--no-log", dest="no_log", action="store_true",
                        help="Desativa a gravação de telemetria em disco.")
    parser.add_argument("--porta", type=int, default=8000, help="Porta local (padrão: 8000).")
    args = parser.parse_args(argv)
    try:
        memoria = KnowledgeBase.load(args.knowledge)
        CitizenAgent(memoria, template=args.template, log_path=None)  # valida base e modelo antes de iniciar
    except (KnowledgeBaseError, TemplateError) as exc:
        print(f"A interface web não pode iniciar com segurança: {exc}", file=sys.stderr)
        return 1
    servico = Servico(memoria, args.template, None if args.no_log else LOG_PATH)
    print(f"Citizen Assist AI (web) em http://127.0.0.1:{args.porta}  |  Ctrl+C para encerrar")
    print(DISCLAIMER)
    try:
        ThreadingHTTPServer(("127.0.0.1", args.porta), criar_manipulador(servico)).serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    except OSError:
        print(f"Não foi possível abrir a porta {args.porta}. Ela pode estar em uso. "
              "Tente: python src/web.py --sem-log --porta 8080", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
