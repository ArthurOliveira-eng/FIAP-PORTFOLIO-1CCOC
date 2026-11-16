"""Create a captioned MP4 from actual CLI output. Requires optional FFmpeg."""
import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = [
    ("Browse the Documents theme", ["1"]),
    ("Direct question with source and confirmation warning", ["How do I recover my gov.br password?"]),
    ("Ambiguous query: ask for clarification", ["CPF"]),
    ("Clarification by record ID", ["CPF", "D04"]),
    ("Empty input: helpful recovery", [""]),
    ("Invalid menu choice", ["99"]),
    ("Out-of-scope question: no invented guidance", ["How do I obtain a Canadian driving licence?"]),
    ("Related navigation: CIN issuing guidance", ["D02"]),
    ("Related navigation: CIN and account security", ["D02", "related", "S05"]),
    ("Related navigation: account levels", ["D02", "related", "S05", "related", "S03"]),
]


def capture(title, inputs):
    result = subprocess.run(
        [sys.executable, str(ROOT / "src" / "sistema.py"), "--no-log"],
        input="\n".join(inputs + ["quit"]) + "\n", text=True,
        capture_output=True, cwd=ROOT, timeout=15,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    # Piped input is not echoed. Pair the captured response with its actual input.
    blocks = result.stdout.split("You: ")
    response = blocks[len(inputs)].strip()
    heading = ["Citizen Assist AI | scripted CLI demonstration", title,
               "Input: " + (inputs[-1] or "[empty]"), ""]
    lines = heading + [line for paragraph in response.splitlines()
                       for line in (textwrap.wrap(paragraph, width=110) or [""])]
    if len(lines) > 32:
        raise RuntimeError("Demo scene is too long; shorten the layout rather than hide its source.")
    return "\n".join(lines), result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--text-only", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    snapshots, transcript = [], []
    for index, (title, inputs) in enumerate(SCENES, 1):
        text, full = capture(title, inputs)
        path = args.output / f"scene-{index:02}.txt"
        path.write_text(text, encoding="utf-8")
        snapshots.append(path)
        transcript.append(f"SCENE {index}: {title}\nInputs: {inputs!r}\n{full}")
    results = ROOT / "tests" / "results.json"
    if results.exists():
        report = json.loads(results.read_text(encoding="utf-8"))
        final = ["Citizen Assist AI | reproducible evaluation", "",
                 "Execution environment: " + report["environment"], ""]
        for template, metrics in report["metrics_by_template"].items():
            final += [template, f"Correct: {metrics['correct']} / {metrics['total']}",
                      f"Accuracy: {metrics['accuracy_rate']:.2%}",
                      f"Mean query time: {metrics['average_query_time_ms']:.6f} ms", ""]
        final += ["Full expected/obtained reports: tests/results.json and tests/results.csv",
                  "", "Scripted demonstration, not a human usability study.",
                  "Independent educational prototype. Confirm guidance with official sources."]
        path = args.output / "scene-results.txt"
        path.write_text("\n".join(final), encoding="utf-8")
        snapshots.append(path)
    (args.output / "demo_transcript.txt").write_text("\n\n".join(transcript), encoding="utf-8")
    if args.text_only:
        return 0
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.exit(2, "Transcript created. Install FFmpeg or use --text-only.\n")
    font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    if not font.exists():
        parser.exit(2, "Video generation requires the documented Linux DejaVu Sans Mono font.\n")
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
