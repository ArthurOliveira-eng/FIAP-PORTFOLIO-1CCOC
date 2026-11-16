"""Ajuda e mensagens de argumentos da linha de comando em pt-BR."""
import argparse
import sys


def traduzir_mensagem(texto):
    substituicoes = {
        "usage: ": "uso: ",
        "positional arguments:": "argumentos posicionais:",
        "optional arguments:": "argumentos opcionais:",
        "options:": "opções:",
        "show this help message and exit": "mostra esta ajuda e encerra",
        "unrecognized arguments:": "argumentos não reconhecidos:",
        "the following arguments are required:": "os seguintes argumentos são obrigatórios:",
        "expected one argument": "esperado um argumento",
        "invalid choice:": "opção inválida:",
        "choose from": "escolha entre",
        "argument ": "argumento ",
        "invalid Path value:": "caminho inválido:",
    }
    for origem, traducao in substituicoes.items():
        texto = texto.replace(origem, traducao)
    return texto


class ArgumentParser(argparse.ArgumentParser):
    """Preserva o analisador padrão e traduz sua apresentação ao usuário."""

    def format_help(self):
        return traduzir_mensagem(super().format_help())

    def format_usage(self):
        return traduzir_mensagem(super().format_usage())

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: erro: {traduzir_mensagem(message)}\n")
