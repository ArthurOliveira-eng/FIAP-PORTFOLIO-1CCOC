# SERVIDOR WEB LOCAL
# Reutiliza o agente do terminal e atende somente em 127.0.0.1.
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import CitizenAgent
from src.cli import ArgumentParser
from src.config import (
    DEFAULT_TEMPLATE,
    DISCLAIMER,
    KNOWLEDGE_PATH,
    LOG_PATH,
    PROMPT_PATHS,
    ROOT,
)
from src.knowledge_base import KnowledgeBase, KnowledgeBaseError
from src.response import TemplateError

from src import ditado
from src.web_service import Servico

WEB_ROOT = ROOT / "web"
MAX_BODY_BYTES = 8192
SESSAO = re.compile(r"[A-Za-z0-9]{8,40}")
ASSET_TYPES = {
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".woff2": "font/woff2",
}


def recursos_estaticos():
    arquivos = {
        "/": (WEB_ROOT / "index.html", "text/html; charset=utf-8"),
        "/index.html": (WEB_ROOT / "index.html", "text/html; charset=utf-8"),
    }
    for arquivo in WEB_ROOT.rglob("*"):
        if arquivo.is_file() and arquivo.suffix in ASSET_TYPES:
            if arquivo.resolve().is_relative_to(WEB_ROOT.resolve()):
                rota = "/" + arquivo.relative_to(WEB_ROOT).as_posix()
                arquivos[rota] = (arquivo, ASSET_TYPES[arquivo.suffix])
    return arquivos


def validar_pedido(pedido):
    if not isinstance(pedido, dict):
        raise ValueError("Envie um objeto JSON.")
    sid = pedido.get("sid", "")
    if not isinstance(sid, str) or not SESSAO.fullmatch(sid):
        raise ValueError("Sessão inválida.")
    modelo = pedido.get("modelo", "")
    tema = pedido.get("tema")
    reiniciar = pedido.get("reiniciar", False)
    if not isinstance(modelo, str):
        raise ValueError("Modelo inválido.")
    if tema is not None and not isinstance(tema, str):
        raise ValueError("Tema inválido.")
    if not isinstance(reiniciar, bool):
        raise ValueError("A opção reiniciar deve ser verdadeira ou falsa.")
    return {
        "sid": sid,
        "texto": pedido.get("texto", ""),
        "modelo": modelo,
        "tema": tema,
        "reiniciar": reiniciar,
    }


def criar_manipulador(servico):
    arquivos = recursos_estaticos()
    consultas = {
        "/api/estado": servico.estado,
        "/api/base": servico.base,
        "/api/indicadores": servico.indicadores,
    }

    class Manipulador(BaseHTTPRequestHandler):
        def enviar(self, codigo, corpo, tipo="application/json; charset=utf-8"):
            dados = (
                corpo
                if isinstance(corpo, bytes)
                else json.dumps(corpo, ensure_ascii=False).encode("utf-8")
            )
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(dados)

        def do_GET(self):
            if self.path in arquivos:
                caminho, tipo = arquivos[self.path]
                try:
                    return self.enviar(200, caminho.read_bytes(), tipo)
                except OSError:
                    return self.enviar(404, {"erro": "Recurso indisponível."})
            if self.path in consultas:
                return self.enviar(200, consultas[self.path]())
            self.enviar(404, {"erro": "Recurso não encontrado."})

        def do_POST(self):
            if self.path == "/api/ditado":
                if self.headers.get("Content-Type") != "application/octet-stream":
                    return self.enviar(415, {"erro": "Formato de áudio inválido."})
                try:
                    tamanho = int(self.headers.get("Content-Length", 0))
                    if not 0 < tamanho <= ditado.LIMITE or tamanho % 2:
                        return self.enviar(413, {"erro": "Gravação inválida ou longa demais."})
                    texto = ditado.transcrever(self.rfile.read(tamanho))
                except ValueError:
                    return self.enviar(400, {"erro": "Gravação inválida."})
                except (ImportError, OSError, RuntimeError):
                    return self.enviar(503, {"erro": "Não foi possível iniciar o reconhecimento local. Confira a instalação do modelo de voz conforme o README."})
                return self.enviar(200, {"texto": texto})
            if self.path != "/api/consultar":
                return self.enviar(404, {"erro": "não encontrado"})
            try:
                tamanho = int(self.headers.get("Content-Length", 0))
                if not 0 < tamanho <= MAX_BODY_BYTES:
                    return self.enviar(413, {"erro": "Pedido muito grande ou vazio."})
                pedido = json.loads(self.rfile.read(tamanho) or b"{}")
                self.enviar(200, servico.consultar(**validar_pedido(pedido)))
            except TemplateError as exc:
                self.enviar(
                    500,
                    {
                        "status": "erro",
                        "mensagem": str(exc),
                        "registros": [],
                        "relacionados": [],
                        "texto": "",
                        "latencia_ms": 0,
                        "tema": None,
                        "log_erro": None,
                    },
                )
            except (ValueError, OSError):
                self.enviar(
                    400, {"erro": "Pedido inválido. Confira os campos da consulta."}
                )

        def log_message(
            self, *args
        ):  # privacidade: sem registro de acessos nem de consultas
            pass

    return Manipulador


def main(argv=None):
    parser = ArgumentParser(
        description="Citizen Assist AI: interface web opcional e local."
    )
    parser.add_argument(
        "--base",
        "--knowledge",
        dest="knowledge",
        type=Path,
        default=KNOWLEDGE_PATH,
        metavar="ARQUIVO",
        help="Arquivo JSON da base de conhecimento.",
    )
    parser.add_argument(
        "--modelo",
        "--template",
        dest="template",
        choices=PROMPT_PATHS,
        default=DEFAULT_TEMPLATE,
        help="Modelo de resposta inicial.",
    )
    parser.add_argument(
        "--sem-log",
        "--no-log",
        dest="no_log",
        action="store_true",
        help="Desativa a gravação de telemetria em disco.",
    )
    parser.add_argument(
        "--porta", type=int, default=8000, help="Porta local (padrão: 8000)."
    )
    args = parser.parse_args(argv)
    try:
        memoria = KnowledgeBase.load(args.knowledge)
        CitizenAgent(
            memoria, template=args.template, log_path=None
        )  # valida base e modelo antes de iniciar
    except (KnowledgeBaseError, TemplateError) as exc:
        print(f"A interface web não pode iniciar com segurança: {exc}", file=sys.stderr)
        return 1
    servico = Servico(memoria, args.template, None if args.no_log else LOG_PATH)
    try:
        with ThreadingHTTPServer(
            ("127.0.0.1", args.porta), criar_manipulador(servico)
        ) as servidor:
            print(
                f"Citizen Assist AI (web) em http://127.0.0.1:{args.porta}  |  Ctrl+C para encerrar"
            )
            print(DISCLAIMER)
            servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    except OSError:
        print(
            f"Não foi possível abrir a porta {args.porta}. Ela pode estar em uso. "
            "Tente: python src/web.py --sem-log --porta 8080",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
