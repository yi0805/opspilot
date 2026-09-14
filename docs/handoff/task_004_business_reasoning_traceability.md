# Task

Task 004 — Business Reasoning and Traceability

## Goal

Extend the Task 003 single-tool workflow into a controlled sequential multi-tool business reasoning service with evidence-based recommendations and deterministic traceability.

## Git context

- **Branch:** `task/004-business-reasoning-traceability`
- **Base commit:** `925854509937005c57136497e58f7221d1724bbd`
- **Final commit:** created with this completion handoff; recorded in the task completion report.
- **Pull request:** none; not opened or pushed.

## Architecture and decisions

The service keeps the Task 003 boundary: OpenAI Responses API function calls are allowlisted and validated in `app.services.llm_tools`, then dispatched to the existing Task 002 query services through the provided SQLAlchemy session. The LLM does not access models or SQLAlchemy directly.

`answer_business_question` keeps a stateless running Responses input beginning with the original user question. Each reasoning round preserves all prior response output and function-call outputs. `parallel_tool_calls=False` remains set, and the implementation processes at most one call per round. Once the model stops requesting a tool, a final request with `tool_choice="none"` uses Responses API JSON Schema structured output.

The final model payload is validated by Pydantic and has `answer`, nullable `recommendation`, and `limitations`. Malformed structured output raises the existing controlled provider error, which the route maps to HTTP 502.

`BusinessQuestionResult` now exposes `answer`, nullable `recommendation`, `evidence`, and `status`. Each `EvidenceRecord` is created by the application only after a successful dispatcher execution and contains the tool name, canonical arguments, returned data, and `synthetic_business_data` source. The model never produces evidence records.

The tool-call limit is `MAX_TOOL_CALLS = 4`. An exact duplicate of a tool name plus validated canonical arguments is not dispatched a second time. The controlled status values are `completed`, `tool_error`, `tool_limit_reached`, and `duplicate_tool_call`. Empty tool data is preserved in evidence; instructions require the model to state the limitation and avoid unsupported recommendations.

## Key changes

- Replaced the Task 003 one-tool cycle with an explicit sequential multi-tool loop.
- Added deterministic evidence records and a recommendation field to the API result.
- Added public canonical tool-argument validation for duplicate-call protection.
- Added tests using mocked OpenAI responses and real isolated SQLite business queries.
- Updated README and marked Task 004 complete in the roadmap.

## Verification

Automated verification was run without a live OpenAI call:

```text
backend> .\.venv\Scripts\python.exe -m pytest
Result: 31 passed; one existing Starlette/TestClient deprecation warning.

backend> .\.venv\Scripts\python.exe -m compileall -q app tests
Result: passed (no output).

frontend> npm test -- --run
Result: 1 test file and 1 test passed.

frontend> npm run lint
Result: passed (no output).

frontend> npm run build
Result: passed; TypeScript and Vite production build completed.

repo> git diff --check
Result: passed (no whitespace errors).
```

## Known limitations

- The model's tool selection and recommendation wording still depend on the configured OpenAI model; tests mock that boundary.
- The workflow is deliberately stateless, non-streaming, and capped at four tools per request.
- Data is synthetic and supports correlation/association only, not causal claims.
- Task 005 frontend work is not implemented.

## Recommended next task

Task 005 — Frontend Experience
