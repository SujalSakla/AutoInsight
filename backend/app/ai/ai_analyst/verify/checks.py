"""Deterministic, best-effort checks run before the model verifier."""
from __future__ import annotations
import re
from typing import Any
from .schemas import Finding


def _df(result):
    return getattr(result, "df", result.get("df") if isinstance(result, dict) else None)


def _sql(result, sql=None):
    return sql or getattr(result, "sql", result.get("sql", "") if isinstance(result, dict) else "")


def _columns(card: dict) -> list[tuple[str, dict]]:
    return [(c["name"], c) for t in card.get("tables", []) for c in t.get("columns", [])]


def _f(level, code, message): return Finding(level=level, code=code, message=message)


def check_empty_result(result, **_) -> Finding | None:
    df = _df(result)
    if df is not None and len(df.index) == 0:
        return _f("warn", "EMPTY_RESULT", "The query returned zero rows.")


def check_truncated(result, **_) -> Finding | None:
    if getattr(result, "truncated", result.get("truncated", False) if isinstance(result, dict) else False):
        return _f("info", "TRUNCATED", "The result reached the row cap and may be incomplete.")


def check_all_null(result, **_) -> Finding | None:
    df = _df(result)
    if df is not None:
        nulls = [str(c) for c in df.columns if df[c].isna().all()]
        if nulls:
            return _f("error", "ALL_NULL_COLUMN", "Result column(s) are entirely NULL: " + ", ".join(nulls))


def check_date_coverage(sql, card, **_) -> Finding | None:
    sql = sql or ""
    years = [int(x) for x in re.findall(r"\b(19\d{2}|20\d{2}|21\d{2})\b", sql)]
    literals = re.findall(r"'(\d{4}(?:-\d\d-\d\d)?)'", sql)
    years += [int(x[:4]) for x in literals if x[:4].isdigit()]
    if not years: return None
    ranges = []
    for name, c in _columns(card):
        if c.get("kind") == "datetime" or "date" in name.lower() or "time" in name.lower():
            if c.get("min") is not None and c.get("max") is not None:
                ranges.append(f"{name}: {c['min']} to {c['max']}")
                maxyear = int(str(c["max"])[:4])
                if any(y > maxyear for y in years):
                    return _f("warn", "DATE_COVERAGE", "Date filter is outside the covered range (" + "; ".join(ranges) + ").")


def check_topn_short(result, sql, **_) -> Finding | None:
    m = re.search(r"\blimit\s+(\d+)", sql or "", re.I)
    df = _df(result)
    if m and df is not None and len(df.index) < int(m.group(1)):
        return _f("info", "TOPN_SHORT", f"LIMIT {m.group(1)} requested but only {len(df.index)} rows were returned.")


def check_sum_ratio(sql, **_) -> Finding | None:
    if re.search(r"\bsum\s*\(\s*[\"`]?[\w.]*?(percent|pct|rate|ratio|change)", sql or "", re.I):
        return _f("warn", "SUM_OF_RATIO", "SUM is applied to a ratio, rate, percent, or change column.")


def check_skewed_avg(sql, card, **_) -> Finding | None:
    for name, c in _columns(card):
        if re.search(r"\bavg\s*\(\s*[\"`]?"+re.escape(name)+r"\b", sql or "", re.I):
            try:
                mean, median, std, maximum = map(float, (c.get("mean"), c.get("median"), c.get("std"), c.get("max")))
                if abs(mean - median) > 3 * max(std, 1e-9) or (abs(median) > 1e-9 and maximum > 20 * abs(median)):
                    return _f("warn", "SKEWED_AVG", f"AVG({name}) may be misleading because the column is heavily skewed.")
            except (TypeError, ValueError):
                pass


def check_join_fanout(sql, **_) -> Finding | None:
    if re.search(r"\bjoin\b", sql or "", re.I) and re.search(r"\bsum\s*\(", sql or "", re.I):
        return _f("warn", "JOIN_FANOUT", "A JOIN with SUM may duplicate rows; compare with the base-table total.")


CHECKS = (check_empty_result, check_truncated, check_all_null, check_date_coverage,
          check_topn_short, check_sum_ratio, check_skewed_avg, check_join_fanout)


def run_checks(question: str, plan: Any, sql: str, result: Any, card: dict) -> list[Finding]:
    findings = []
    for check in CHECKS:
        finding = check(question=question, plan=plan, sql=sql, result=result, card=card)
        if finding: findings.append(finding)
    return findings
