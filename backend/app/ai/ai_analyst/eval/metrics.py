"""Aggregate metrics for evaluation reports."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class Metrics:
    total: int
    exact_match: float
    execution_success: float
    numeric_accuracy: float
    verifier_catch_rate: float
    mean_latency_ms: float

    def to_dict(self) -> dict:
        return asdict(self)


def compute_metrics(results: Iterable[dict]) -> Metrics:
    rows = list(results)
    n = len(rows)
    if not n:
        return Metrics(0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return Metrics(
        n,
        sum(bool(r.get("exact_match")) for r in rows) / n,
        sum(bool(r.get("execution_success")) for r in rows) / n,
        sum(float(r.get("numeric_accuracy", 0)) for r in rows) / n,
        sum(bool(r.get("verifier_caught")) for r in rows) / n,
        sum(float(r.get("latency_ms", 0)) for r in rows) / n,
    )
