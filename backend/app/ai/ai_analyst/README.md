# AI Analyst (Phase 2)

This package ports the POC router, planner, profiler, read-only DuckDB executor,
SQL retry loop, and synthesizer behind `/api/ai`: create a session, add files,
inspect the session/card, chat, and delete.

The current `development_identity` dependency is deliberately temporary and is
**not authentication**. It supplies the owner metadata needed to isolate
sessions while the host application has no auth layer. Production is blocked
until a real authenticated-user dependency replaces it. Sessions expire after
one hour; uploads are allowlisted and capped at 25 MiB. Model prompts use the
ported prompt templates and query results are capped at 1,000 rows.

Set `NVIDIA_API_KEY` (and optionally `LLM_PROVIDER`) before asking questions.
Missing keys fail lazily with a typed 503; importing the module remains offline-safe.
Exact configuration names are `AI_SESSION_TTL_HOURS=24`,
`AI_MAX_UPLOAD_MB=25`, `AI_LLM_TIMEOUT_S=60`,
`AI_SEND_SAMPLE_ROWS=true`, and `AI_SEND_TOP_VALUES=true`.
`AI_RATE_LIMIT_PER_MINUTE` defaults to 20 and `AI_PRIVACY_DEFAULT` controls
privacy metadata. Legacy seconds/bytes aliases remain supported.
