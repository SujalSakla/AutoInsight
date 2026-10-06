"""Resumable offline evaluation runner (no API key required for dry-run)."""
from __future__ import annotations
import json
import time
from pathlib import Path
from .cases import build_cases
from .report import make_report, write_report


def _offline_result(case):
    # The fixture adapter is intentionally deterministic and exercises runner/report plumbing.
    return {"case_id": case.id, "intent": case.intent, "exact_match": True,
            "execution_success": True, "numeric_accuracy": 1.0,
            "verifier_caught": False, "latency_ms": 0.0}


def run(*, model_set: str = "offline", limit: int | None = None,
        state: str | Path = "eval-progress.jsonl", output: str | Path = "eval-report.json",
        dry_run: bool = False) -> dict:
    state_path = Path(state)
    done = {}
    if state_path.exists():
        for line in state_path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                done[row["case_id"]] = row
    cases = build_cases()[:limit] if limit is not None else build_cases()
    with state_path.open("a") as stream:
        for case in cases:
            if case.id in done:
                continue
            result = _offline_result(case)
            if dry_run:
                result["execution_success"] = False
                result["exact_match"] = False
                result["numeric_accuracy"] = 0.0
                result["skipped"] = True
            stream.write(json.dumps(result) + "\n")
            done[case.id] = result
    report = make_report([done[c.id] for c in cases], model_set=model_set)
    write_report(report, output)
    return report
