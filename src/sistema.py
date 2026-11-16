"""Interface textual. Execute de qualquer pasta: python /caminho/para/src/sistema.py."""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import CitizenAgent
from src.cli import ArgumentParser
from src.config import DEFAULT_TEMPLATE, DISCLAIMER, KNOWLEDGE_PATH, LOG_PATH, PROMPT_PATHS
from src.knowledge_base import KnowledgeBase, KnowledgeBaseError
from src.response import TemplateError


def main(argv=None):
    parser = ArgumentParser(description="Citizen Assist AI: orientação independente ao cidadão.")
    parser.add_argument("--base", "--knowledge", dest="knowledge", type=Path, default=KNOWLEDGE_PATH,
                        metavar="ARQUIVO", help="Arquivo JSON da base de conhecimento.")
    parser.add_argument("--modelo", "--template", dest="template", choices=PROMPT_PATHS,
                        default=DEFAULT_TEMPLATE, help="Modelo de resposta utilizado.")
    parser.add_argument("--sem-log", "--no-log", dest="no_log", action="store_true",
                        help="Desativa a gravação de telemetria em disco.")
    args = parser.parse_args(argv)
    try:
        memory = KnowledgeBase.load(args.knowledge)
        agent = CitizenAgent(memory, template=args.template, log_path=None if args.no_log else LOG_PATH)
        print("Citizen Assist AI\n" + DISCLAIMER)
        print("\nTemas disponíveis:")
        for number, theme in enumerate(memory.themes, 1):
            print(f"  {number}. {theme}")
        print("\nFaça uma pergunta, escolha o número de um tema ou digite um ID de registro.")
        print("Comandos: relacionados | voltar | ajuda | sair (ou 0)")
        while True:
            try:
                query = input("\nVocê: ")
            except (EOFError, KeyboardInterrupt):
                print("\nSessão encerrada.")
                return 0
            answer = agent.handle(query)
            print("\n" + answer.text)
            if answer.log_error:
                print("Aviso de registro: " + answer.log_error, file=sys.stderr)
            if answer.status == "quit":
                return 0
    except (KnowledgeBaseError, TemplateError) as exc:
        print(f"O Citizen Assist AI não pode iniciar ou responder com segurança: {exc}", file=sys.stderr)
        print("Confira o arquivo de conhecimento e os modelos; nenhuma orientação foi inventada.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
