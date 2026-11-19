"""Reconhecimento local opcional de áudio PCM mono, 16 kHz."""
import io
import json
import subprocess
import wave
from array import array
import os
from pathlib import Path
from threading import Lock

MODELO = Path(os.getenv("LOCALAPPDATA") or Path.home() / ".cache") / "PolisHelp" / "vosk-model-small-pt-0.3"
WHISPER = MODELO.parent / "whisper"
LIMITE = 16000 * 2 * 30
_lock = Lock()
_modelo = None


def transcrever(audio):
    global _modelo
    if (WHISPER / "Release" / "whisper-cli.exe").is_file() and (WHISPER / "ggml-small-q5_1.bin").is_file():
        with _lock:
            return transcrever_whisper(audio)
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


def transcrever_whisper(audio):
    """Normaliza fala baixa e envia WAV pela memória ao processo local."""
    amostras = array("h")
    amostras.frombytes(audio)
    pico = max((abs(v) for v in amostras), default=0)
    rms = (sum(v * v for v in amostras) / max(1, len(amostras))) ** .5
    if rms < 4:
        return ""
    ganho = min(6, 2000 / rms, 30000 / max(1, pico))
    normalizado = array("h", (int(v * ganho) for v in amostras)).tobytes()
    arquivo = io.BytesIO()
    with wave.open(arquivo, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(normalizado)
    # Um nome de saída sem flags de exportação mantém a resposta em stdout no Windows.
    comando = [
        str(WHISPER / "Release" / "whisper-cli.exe"),
        "-m", str(WHISPER / "ggml-small-q5_1.bin"),
        "-l", "pt", "-f", "-", "-nt", "-of", "transcricao", "-t", "4",
    ]
    try:
        resultado = subprocess.run(
            comando, input=arquivo.getvalue(), capture_output=True, timeout=90,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Tempo de transcrição excedido.") from exc
    if resultado.returncode:
        raise RuntimeError("O reconhecimento local não concluiu a transcrição.")
    return resultado.stdout.decode("utf-8", errors="replace").strip()[:500]
