"""Execute predefined task scripts, not a human usability study."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from statistics import mean
from time import perf_counter
from src.config import ROOT
from src.evaluation import write_json


def run_tasks():
    tasks = json.loads((ROOT / "tests" / "usability_tasks.json").read_text(encoding="utf-8"))
    rows = []
    for task in tasks:
        started = perf_counter()
        result = subprocess.run(
            [sys.executable, str(ROOT / "src" / "sistema.py"), "--no-log"],
            input="\n".join(task["inputs"]) + "\n", capture_output=True,
            text=True, cwd=ROOT, timeout=15,
        )
        elapsed = (perf_counter() - started) * 1000
        success = result.returncode == 0 and all(term in result.stdout for term in task["expected"])
        rows.append({
            **task, "success": success, "script_actions": len(task["inputs"]) - 1,
            "process_time_ms": round(elapsed, 6), "return_code": result.returncode,
            "obtained_transcript": result.stdout, "stderr": result.stderr,
        })
    report = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "environment": "github-actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "local",
        "study_type": "automated task script", "human_participants": 0,
        "task_completion_rate": sum(row["success"] for row in rows) / len(rows),
        "average_script_actions": mean(row["script_actions"] for row in rows),
        "average_process_time_ms": mean(row["process_time_ms"] for row in rows),
        "limitations": "Script execution is not human task time, satisfaction, accessibility validation, "
        "or independent evidence of comprehension. Difficulties are anticipated interaction costs, "
        "not observations from participants.",
        "tasks": rows,
    }
    write_json(ROOT / "tests" / "usability_results.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "tasks"}, indent=2))
    return 0 if all(row["success"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(run_tasks())
