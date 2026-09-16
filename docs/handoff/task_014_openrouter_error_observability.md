# Task 014 — Safe OpenRouter Provider Error Observability

## Status

Complete as a repository-only change. Subsequent Task 020 production verification confirmed the OpenRouter migration completed without a provider-failure warning; Task 021 records that verified state.

## Goal

Add minimal, security-safe server-side logging for OpenRouter SDK request failures while preserving the public generic HTTP 502 provider-error response.

## Git context

- **Branch:** `task/014-openrouter-error-observability`
- **Base commit:** `af79175d8827cffdbab1bbf569d29e6d237ce3d3`
- **Final commit:** this handoff's containing commit
- **Pull request:** pending creation

## Key changes

- Added standard-library warning logging at the reasoning and final Responses API request boundaries.
- Logs contain only `stage`, exception class name, an integer HTTP `status_code` in the 100–599 range when available, and a `request_id` matching `[A-Za-z0-9._:-]{1,128}` when available. Missing or invalid metadata is recorded as `None`.
- Kept exception messages, bodies, response objects, headers, prompts, tool data, request payloads, secrets, and stack traces out of the log call.
- Added focused fake-client tests for both request stages, safe metadata, absent metadata, sensitive exception content, and unchanged `LLMProviderError` behavior.

## Verification

- `python -m ruff check app tests` — passed.
- `python -m mypy app` — passed: 23 source files, no issues.
- `python -m pytest` — passed: 40 tests. One pre-existing pytest-asyncio configuration deprecation warning and one Starlette/TestClient deprecation warning were reported.
- `python -m compileall -q app tests` — passed.
- `git diff --check` — passed.

## Known limitations and decisions

- No provider request was made. Tests use local fake clients only.
- No AWS, Terraform, SSM, deployment, or production configuration was accessed or changed.
- This task intentionally does not alter the API route, provider model, routing configuration, or `provider.require_parameters` option.

## Recommended next task

Review and merge the Task 014 pull request, then perform any production smoke test only in a separately authorized operational task.
