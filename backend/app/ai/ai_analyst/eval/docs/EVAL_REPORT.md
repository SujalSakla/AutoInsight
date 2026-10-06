# AI Analyst evaluation report

## Status

The offline/dry-run harness is wired and reproducible. Real model numbers are
pending an API key and a model-enabled run; dry-run numbers must not be treated
as quality measurements.

Run:

```bash
python -m app.ai.ai_analyst.eval run --config eval/configs/A.yaml \
  --cases eval/cases/core.yaml --out eval-report.json --dry-run
python -m app.ai.ai_analyst.eval report --input eval-report.json --out eval-report.json
```

Reports include overall and category metrics: routing, plan validity, SQL
first-attempt success/retries, execution, verifier catch and false-positive
rates, correction and grounding failures, p50/p95 stage/total latency, tokens,
errors, and fallbacks.
