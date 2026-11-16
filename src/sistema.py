"""Text interface. Run from any directory: python /path/to/src/sistema.py."""
import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import CitizenAgent
from src.config import DEFAULT_TEMPLATE, DISCLAIMER, KNOWLEDGE_PATH, LOG_PATH, PROMPT_PATHS
from src.knowledge_base import KnowledgeBase, KnowledgeBaseError
from src.response import TemplateError


def main(argv=None):
    parser = argparse.ArgumentParser(description="Citizen Assist AI: independent citizen guidance.")
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE_PATH)
    parser.add_argument("--template", choices=PROMPT_PATHS, default=DEFAULT_TEMPLATE)
    parser.add_argument("--no-log", action="store_true", help="Disable all on-disk telemetry.")
    args = parser.parse_args(argv)
    try:
        memory = KnowledgeBase.load(args.knowledge)
        agent = CitizenAgent(memory, template=args.template, log_path=None if args.no_log else LOG_PATH)
        print("Citizen Assist AI\n" + DISCLAIMER)
        print("\nAvailable themes:")
        for number, theme in enumerate(memory.themes, 1):
            print(f"  {number}. {theme}")
        print("\nAsk a question, choose a theme number, or enter a record ID.")
        print("Commands: related | back | help | quit (or 0)")
        while True:
            try:
                query = input("\nYou: ")
            except (EOFError, KeyboardInterrupt):
                print("\nSession ended.")
                return 0
            answer = agent.handle(query)
            print("\n" + answer.text)
            if answer.log_error:
                print("Logging notice: " + answer.log_error, file=sys.stderr)
            if answer.status == "quit":
                return 0
    except (KnowledgeBaseError, TemplateError) as exc:
        print(f"Citizen Assist AI cannot start or answer safely: {exc}", file=sys.stderr)
        print("Check the knowledge file and templates; no guidance was invented.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
