"""Cria um MP4 legendado da saída real da interface. Requer FFmpeg opcional."""
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.cli import ArgumentParser

SCENES = [
    ("Consultar o tema Documentos", ["1"]),
    ("Pergunta direta com fonte e aviso de confirmação", ["Como recuperar minha senha do gov.br?"]),
    ("Consulta ambígua: solicitar esclarecimento", ["CPF"]),
    ("Esclarecimento pelo ID do registro", ["CPF", "D04"]),
    ("Entrada vazia: retomada da consulta", [""]),
    ("Opção inválida do menu", ["99"]),
    ("Pergunta fora do escopo: sem inventar orientações", ["Como obter uma carteira de motorista canadense?"]),
    ("Navegação relacionada: emissão da CIN", ["D02"]),
    ("Navegação relacionada: CIN e segurança da conta", ["D02", "relacionados", "S05"]),
    ("Navegação relacionada: níveis da conta", ["D02", "relacionados", "S05", "relacionados", "S03"]),
]


def capture(title, inputs):
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / "src" / "sistema.py"), "--sem-log"],
        input="\n".join(inputs + ["sair"]) + "\n", encoding="utf-8",
        capture_output=True, cwd=ROOT, timeout=15,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    # A entrada por canal não aparece na saída. Associa a resposta à entrada utilizada.
    blocks = result.stdout.split("Você: ")
    response = blocks[len(inputs)].strip()
    heading = ["Citizen Assist AI | demonstração por roteiro no terminal", title,
               "Entrada: " + (inputs[-1] or "[vazia]"), ""]
    lines = heading + [line for paragraph in response.splitlines()
                       for line in (textwrap.wrap(paragraph, width=110) or [""])]
    if len(lines) > 32:
        raise RuntimeError("Cena longa demais; reduza o texto sem ocultar a fonte.")
    return "\n".join(lines), result.stdout


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--saida", "--output", dest="output", type=Path, default=ROOT / "artifacts",
                        metavar="PASTA", help="Pasta de saída da demonstração.")
    parser.add_argument("--somente-texto", "--text-only", dest="text_only", action="store_true",
                        help="Gera a transcrição sem criar vídeo.")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    snapshots, transcript = [], []
    for index, (title, inputs) in enumerate(SCENES, 1):
        text, full = capture(title, inputs)
        path = args.output / f"scene-{index:02}.txt"
        path.write_text(text, encoding="utf-8")
        snapshots.append(path)
        transcript.append(f"CENA {index}: {title}\nEntradas: {inputs!r}\n{full}")
    results = ROOT / "tests" / "results.json"
    if results.exists():
        report = json.loads(results.read_text(encoding="utf-8"))
        final = ["Citizen Assist AI | avaliação reproduzível", "",
                 "Ambiente de execução: " + report["environment"], ""]
        for template, metrics in report["metrics_by_template"].items():
            final += [template, f"Corretas: {metrics['correct']} / {metrics['total']}",
                      f"Taxa de acerto: {metrics['accuracy_rate']:.2%}",
                      f"Tempo médio de consulta: {metrics['average_query_time_ms']:.6f} ms", ""]
        final += ["Relatórios completos de resultados esperados/obtidos: tests/results.json e tests/results.csv",
                  "", "Demonstração por roteiro, sem estudo com participantes humanos.",
                  "Protótipo educacional independente. Confirme as orientações nas fontes oficiais."]
        path = args.output / "scene-results.txt"
        path.write_text("\n".join(final), encoding="utf-8")
        snapshots.append(path)
    (args.output / "demo_transcript.txt").write_text("\n\n".join(transcript), encoding="utf-8")
    if args.text_only:
        return 0
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.exit(2, "Transcrição criada. Instale o FFmpeg ou use --somente-texto.\n")
    font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    if not font.exists():
        parser.exit(2, "A geração de vídeo exige a fonte DejaVu Sans Mono no caminho Linux documentado.\n")
    clips = []
    for index, snapshot in enumerate(snapshots, 1):
        clip = args.output / f"clip-{index:02}.mp4"
        video_filter = (
            f"drawtext=fontfile='{font}':textfile='{snapshot.resolve()}':expansion=none:"
            "fontcolor=white:fontsize=18:x=40:y=30:line_spacing=3"
        )
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
             "-i", "color=c=0x151515:s=1280x720:r=12", "-t", "10", "-vf", video_filter,
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(clip)],
            check=True, timeout=90,
        )
        clips.append(clip)
    manifest = args.output / "clips.txt"
    manifest.write_text("".join(f"file '{clip.name}'\n" for clip in clips), encoding="utf-8")
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", str(manifest), "-c", "copy", str(args.output / "citizen-assist-demo.mp4")],
        check=True, timeout=90,
    )
    print(args.output / "citizen-assist-demo.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
