"""Reconhecimento local opcional de áudio PCM mono, 16 kHz."""
import json
import os
from pathlib import Path
from threading import Lock

MODELO = Path(os.getenv("LOCALAPPDATA") or Path.home() / ".cache") / "PolisHelp" / "vosk-model-small-pt-0.3"
LIMITE = 16000 * 2 * 30
_lock = Lock()
_modelo = None


def transcrever(audio):
    global _modelo
    from vosk import KaldiRecognizer, Model

    with _lock:
        if _modelo is None:
            if not MODELO.is_dir():
                raise FileNotFoundError(MODELO)
            _modelo = Model(str(MODELO))
        leitor = KaldiRecognizer(_modelo, 16000)
        partes = []
        for inicio in range(0, len(audio), 8000):
            if leitor.AcceptWaveform(audio[inicio:inicio + 8000]):
                partes.append(json.loads(leitor.Result())["text"])
        partes.append(json.loads(leitor.FinalResult())["text"])
        return " ".join(filter(None, partes))[:500]
