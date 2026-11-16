# Local validation

Executed on Windows with Python 3.14 on 2026-11-16. The tested source commit is recorded in tests/results.json.

| Check | Command | Result |
| --- | --- | --- |
| Regression suite | `py -3 -m unittest discover -s tests -v` | 19 tests passed |
| Retrieval and response evaluation | `py -3 -m src.evaluation` | 31/31 cases passed for each template; 62 total |
| Scripted usability | `py -3 -m tests.run_usability` | 8/8 tasks completed |
| Demonstration transcript | `py -3 scripts/create_demo.py --text-only` | Captured all 10 scenes and generated the metrics scene |

Mean measured query times were 0.529052 ms for template A and 0.565581 ms for template B. These timings describe this run and machine, not a performance guarantee. The usability scripts averaged 2.5 prescribed actions and 98.634188 ms per subprocess. They do not measure human reading time or satisfaction.

The regression suite exercises the actual terminal interface, including a complete consultation flow, missing knowledge files, execution outside the repository, and end-of-input handling. It also checks both templates, related navigation, ambiguity, theme filters, privacy-safe logs, logging failure, stale records, schema validation, and atomic updates.

Machine-readable reports and expected/obtained answers are stored in tests/results.json, tests/results.csv, tests/template_comparison.json, and tests/usability_results.json. The transcript is generated locally at artifacts/demo_transcript.txt; artifacts/ is intentionally ignored by Git.

FFmpeg was not available locally, so this validation generated the text demonstration only. MP4 generation remains available through the Linux GitHub Actions workflow. A YouTube upload, team name, and member RMs remain submission tasks.

The assignment explicitly requires docs/uso_ia.md to identify AI tools and critical validation. That disclosure remains part of the deliverable. The application itself uses deterministic retrieval and templates without external model calls.
