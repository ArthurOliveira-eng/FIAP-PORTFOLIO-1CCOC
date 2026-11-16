# Demonstration and YouTube handoff

An automated demonstration can be generated from actual CLI subprocess output. It is captioned and silent, approximately 110 seconds with the evaluation scene. It demonstrates menu browsing, a direct question and official source, CPF ambiguity and clarification, empty input, an invalid option, an out-of-scope question, three related subjects, and measured metrics when available.

```bash
python -m unittest discover -s tests -v
python -m src.evaluation
python -m tests.run_usability
python scripts/create_demo.py --text-only
```

These commands need only Python. The transcript is written to artifacts/demo_transcript.txt. For an MP4 on Linux, additionally install FFmpeg and the DejaVu Sans Mono font (the generator checks /usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf), then run:

```bash
python scripts/create_demo.py
```

The GitHub Actions workflow installs these optional video tools and uploads citizen-assist-evidence, including artifacts/citizen-assist-demo.mp4. Download it from the completed run's Artifacts section. Failure of optional video generation must not be represented as a successful video.

For a human screen recording, run the CLI, use the same synthetic questions from the task scripts, explain source/date/warnings, follow D02 → related → S05 → related → S03, show actual evaluation reports, and mention limitations and AI assistance. Optional narration can explain the deterministic agent and template comparison. Show team/RMs after the team confirms them.

The team must upload the actual video through its YouTube account, select Unlisted visibility, verify the URL in a signed-out browser, and put the actual URL in README.md and SUBMISSION_LINKS.TXT. No YouTube account connection or upload tool is available here. Do not use a placeholder as evidence of a published video. The generated MP4 is an evidence artifact, not a human usability study.
