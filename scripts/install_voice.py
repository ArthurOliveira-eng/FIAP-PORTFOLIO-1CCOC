"""Instala o reconhecimento local no Windows com artefatos oficiais verificados."""
import hashlib
import os
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(os.environ["LOCALAPPDATA"]) / "PolisHelp" / "whisper"
ROOT.mkdir(parents=True, exist_ok=True)
FILES = [
    ("runtime.zip",
     "https://github.com/ggml-org/whisper.cpp/releases/download/v1.9.2/whisper-bin-x64.zip",
     "49dcc16de826f20bd53d44f947a1ae49dfa81f86cad67a64d80820cb192d674a"),
    ("ggml-small-q5_1.bin",
     "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small-q5_1.bin",
     "ae85e4a935d7a567bd102fe55afc16bb595bdb618e11b2fc7591bc08120411bb"),
]
for name, url, expected in FILES:
    path = ROOT / name
    if not path.exists():
        print(f"Baixando {name}...", flush=True)
        urllib.request.urlretrieve(url, path)
    with path.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != expected:
        raise RuntimeError(f"Arquivo inconsistente: {path}. Remova-o e execute novamente.")
with zipfile.ZipFile(ROOT / "runtime.zip") as archive:
    archive.extractall(ROOT)
print(f"Reconhecimento local instalado em {ROOT}. Reinicie o aplicativo.")
