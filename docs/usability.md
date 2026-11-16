# Scripted usability evaluation

The assignment permits a task script instead of a participant. Eight scripts are stored in tests/usability_tasks.json and execute the real CLI in subprocesses through python -m tests.run_usability. Results include actual stdout, exit code, completion checks, action counts, and process wall time. There are no human participants.

| Task | Intended outcome | Anticipated friction |
| --- | --- | --- |
| U01 | Browse documents then view CIN guidance | Record IDs require a second selection |
| U02 | Recover forgotten gov.br password | Recovery happens only through the official service |
| U03 | Resolve CPF ambiguity | Broad query requires clarification |
| U04 | Recover from empty/invalid menu input | Extra interactions before useful guidance |
| U05 | Recognize unsupported foreign service | Cannot fulfill a request outside this base |
| U06 | Navigate D02 → S05 → S03 | Requires related subject ID choices |
| U07 | Leave theme before another-theme question | Active theme filter can hide otherwise relevant results |
| U08 | Prepare consumer complaint evidence | Evidence must stay outside this assistant |

Indicators: completed scripts / total scripts, average prescribed actions excluding quit, and mean subprocess wall time. These are automation indicators. They do not measure human completion time, comprehension, cognitive load, assistive-technology compatibility, or satisfaction. Difficulties are design observations/anticipated friction, not quotations from test users.

Interpret results by inspecting failed transcripts before claiming task completion. A fully passing script suite shows those paths are operational, but can still miss confusing language or navigation. A follow-up study should recruit at least one consenting user, use synthetic information only, record consent and task difficulties without unnecessary identity data, and report real completion/comprehension outcomes. Improve active-theme visibility and offer numbered clarification choices based on observed difficulties.
