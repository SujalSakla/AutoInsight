"""JSON and Markdown report generation."""
from __future__ import annotations
import json
from pathlib import Path
from .metrics import compute_metrics


def make_report(results: list[dict], *, model_set: str = "offline") -> dict:
    return {"model_set": model_set, "metrics": compute_metrics(results).to_dict(), "results": results}


def write_report(report: dict, output: str | Path) -> tuple[Path, Path]:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    json_path = path if path.suffix == ".json" else path.with_suffix(".json")
    md_path = json_path.with_suffix(".md")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    m = report["metrics"]
    lines = ["# AI Analyst Evaluation", "", f"**Model set:** `{report['model_set']}`", "",
             "| Metric | Value |", "|---|---:|"]
    lines += [f"| {k.replace('_', ' ').title()} | {v:.4f} |" if isinstance(v, float)
              else f"| {k.replace('_', ' ').title()} | {v} |" for k, v in m.items()]
    lines += ["", "## Cases", "", "| Case | Intent | Exact | Success | Latency (ms) |",
              "|---|---|---:|---:|---:|"]
    lines += [f"| {r.get('case_id')} | {r.get('intent')} | {str(bool(r.get('exact_match'))).lower()} | "
              f"{str(bool(r.get('execution_success'))).lower()} | {r.get('latency_ms', 0):.2f} |"
              for r in report["results"]]
    md_path.write_text("\n".join(lines) + "\n")
    return json_path, md_path
