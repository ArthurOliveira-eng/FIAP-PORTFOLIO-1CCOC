"""Protege silêncio, ganho e transporte de áudio sem gravar arquivos."""
import io
import subprocess
import unittest
import wave
from array import array
from unittest.mock import patch
from src.ditado import transcrever_whisper


class DitadoTests(unittest.TestCase):
    @patch("src.ditado.subprocess.run")
    def test_silencio_nao_gera_transcricao(self, run):
        self.assertEqual(transcrever_whisper(bytes(3200)), "")
        run.assert_not_called()

    @patch("src.ditado.subprocess.run")
    def test_audio_baixo_normalizado_com_saida_em_memoria(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "Como acessar o SUS?".encode(), b"")
        pcm = array("h", [100, -100] * 8000).tobytes()
        self.assertEqual(transcrever_whisper(pcm), "Como acessar o SUS?")
        args, kwargs = run.call_args
        self.assertIn("pt", args[0])
        self.assertIn("transcricao", args[0])
        with wave.open(io.BytesIO(kwargs["input"]), "rb") as wav:
            self.assertEqual((wav.getframerate(), wav.getnchannels()), (16000, 1))
            samples = array("h", wav.readframes(wav.getnframes()))
        self.assertEqual(max(samples), 600)

    @patch("src.ditado.subprocess.run", side_effect=subprocess.TimeoutExpired("whisper", 90))
    def test_timeout_apresenta_erro_controlado(self, run):
        with self.assertRaises(RuntimeError):
            transcrever_whisper(array("h", [100, -100] * 8000).tobytes())
