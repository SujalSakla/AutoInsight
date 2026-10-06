from __future__ import annotations
import os, re
from dataclasses import dataclass
from .schemas import Verification


def max_corrections() -> int:
    try: return max(0, int(os.getenv("AI_MAX_CORRECTIONS", "2")))
    except ValueError: return 2


def verifier_enabled() -> bool:
    return os.getenv("AI_VERIFIER_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def normalized_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", (sql or "").strip().rstrip(";")).lower()


@dataclass
class CorrectionOutcome:
    outcome: object
    verification: Verification | None
    findings: list
    corrections: int
    status: str
    confidence: str
    caveat: str | None = None


def corrective_loop(initial, *, verify, regenerate, findings=None, enabled=None, limit=None):
    """Run verification/correction while guarding duplicate SQL and exhaustion.

    ``regenerate`` receives the previous outcome, verification, and findings.
    """
    findings = list(findings or [])
    enabled = verifier_enabled() if enabled is None else enabled
    limit = max_corrections() if limit is None else max(0, limit)
    outcome = initial
    seen = {normalized_sql(getattr(initial, "result", initial).sql if hasattr(getattr(initial, "result", initial), "sql") else "")}
    corrections = 0
    verification = None
    if not enabled:
        return CorrectionOutcome(outcome, None, findings, 0, "pass", "high")
    while True:
        verification = verify(outcome, findings)
        if verification.verdict != "incorrect":
            status = "ambiguous" if verification.verdict == "ambiguous" else "pass"
            confidence = "medium" if status == "ambiguous" or any(f.level in {"warn", "error"} for f in findings) else "high"
            return CorrectionOutcome(outcome, verification, findings, corrections, status, confidence)
        if corrections >= limit:
            return CorrectionOutcome(outcome, verification, findings, corrections, "fail", "low",
                                     "The answer could not be fully verified; please treat it as approximate.")
        candidate = regenerate(outcome, verification, findings)
        candidate_sql = getattr(getattr(candidate, "result", candidate), "sql", "")
        if normalized_sql(candidate_sql) in seen:
            return CorrectionOutcome(outcome, verification, findings, corrections, "fail", "low",
                                     "The answer could not be verified because correction produced the same query.")
        seen.add(normalized_sql(candidate_sql))
        outcome = candidate
        corrections += 1
