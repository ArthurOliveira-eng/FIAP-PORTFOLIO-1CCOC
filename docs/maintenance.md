# Knowledge maintenance

Back up data/knowledge_base.json before editing. Reopen the official reference, compare the guidance and warning, then set verification_date to the real review date in YYYY-MM-DD. Do not update dates without a review. Use stable IDs; check related IDs in both directions when renaming/removing records.

To add or correct records, edit the JSON and run the full test commands, or use the administrative helper from the repository root:

```python
import json
from src.config import KNOWLEDGE_PATH
from src.knowledge_base import save_record

record = json.loads(open('reviewed_record.json', encoding='utf-8').read())
save_record(KNOWLEDGE_PATH, record)                # new ID
# save_record(KNOWLEDGE_PATH, record, replace=True) # existing ID
```

The helper requires the existing base, accepts a complete record, validates the entire resulting graph, and atomically replaces the same file. Validation failure preserves the original file. It does not fetch sources or perform factual review. There is no public mutation command in the citizen interface.

After changes, update affected evaluation cases with justified expected answers and add independent paraphrases. Rerun unit tests, evaluation, and task scripts. Avoid changing expected answers just to conceal a regression. Paths and thresholds are centralized in src/config.py. Template changes need a new clear version name and an A/B evaluation.

Troubleshooting: missing/empty/malformed files produce a controlled startup error. Restore a valid base. A missing/malformed template stops safe answering. Logging failures produce a visible notice while guidance remains usable. Use --no-log for demos or to avoid any stored telemetry. The application requires Python 3.10+; py -3 may be the launcher on Windows.
