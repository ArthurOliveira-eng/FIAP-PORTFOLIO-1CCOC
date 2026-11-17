"""Inicia a interface web local sem instalar dependências extras."""
from src.web import main

if __name__ == '__main__':
    raise SystemExit(main(['--sem-log']))
