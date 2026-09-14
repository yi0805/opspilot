# Task

Task 003 — LLM Tool Calling

## Goal

Allow an LLM to answer one simple business question by selecting one deterministic Task 002 business query as a structured tool.

## Git context

- **Branch:** `task/003-llm-tool-calling`
- **Base commit:** `048ea559c241fe589d00c81f2614a4821620d12e`
- **Final commit:** created with this completion handoff; reported in the task completion report.
- **Pull request:** none; not opened or pushed

## Architecture and integration

The implementation is explicit: the OpenAI Responses API selects a tool, `app.services.llm_tools` validates and dispatches it, and the existing `app.services.business_queries` functions query through the supplied SQLAlchemy session. The LLM layer never queries SQLAlchemy models directly.

The official `openai` Python SDK is configured through `OPENAI_API_KEY` and `OPENAI_MODEL`; the model defaults to `gpt-5.6-luna`. No provider abstraction or agent framework was added.

The four strict function-tool schemas are `get_product_details`, `query_sales`, `query_inventory`, and `query_campaigns`. Nullable fields express optional values while preserving OpenAI strict-schema requirements, and parallel tool calls are disabled. The dispatcher has an explicit allowlist, rejects malformed JSON, unknown fields/tools, and invalid or inverted date ranges, converts valid dates to Python `date` values, and JSON-safely serializes `Decimal`, `date`, and `datetime` results.

`POST /api/agent/query` accepts a non-blank question up to 500 characters and returns a stable `answer`, `tool_used`, `tool_arguments`, and status. Missing configuration returns HTTP 503; provider failures return HTTP 502.

## Key files changed

- `backend/app/services/llm_tools.py`
- `backend/app/services/llm_agent.py`
- `backend/app/api/routes/agent.py`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/tests/test_llm_tools.py`
- `backend/tests/test_llm_agent.py`
- `backend/pyproject.toml` and `backend/.env.example`
- `README.md` and `ROADMAP.md`

## Verification

Automated verification uses mocked OpenAI Responses API calls and real deterministic Task 002 queries against isolated SQLite:

```text
backend> .\.venv\Scripts\python.exe -m pytest
Result: 23 passed; two existing FastAPI/TestClient deprecation warnings.

backend> .\.venv\Scripts\python.exe -m compileall -q app tests
Result: passed (no output).

frontend> npm test -- --run
Result: 1 test file and 1 test passed.

frontend> npm run lint
Result: passed (no output).

frontend> npm run build
Result: passed; TypeScript build and Vite production build completed.

repo> git diff --check
Result: passed (no whitespace errors).
```

No live OpenAI API call was performed; verification used mocked provider responses only.

## Known limitations

- One tool call per interaction only; attempted multiple calls return a controlled unsupported result.
- No conversation history, streaming, recommendations, evidence/source traceability, or multi-tool orchestration.
- Task 004 is not implemented.

## Recommended next task

Task 004 — Business Reasoning and Traceability
