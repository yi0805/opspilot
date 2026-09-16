# Task 010 — OpenRouter Provider Migration

## Status

Complete as a repository change. Subsequent Task 020 production verification confirmed the migration is deployed; Task 021 records that verified state.

## Goal

Migrate the existing Responses API agent integration from direct OpenAI API access to OpenRouter without changing agent workflow, tools, result contracts, or infrastructure outside provider-secret configuration.

## Git context

- **Branch:** `task/010-openrouter-provider-migration`
- **Base commit:** `25b9c67f59e4187d5e263f3405c09a4b8db4363c`
- **Final commit:** the commit that contains this handoff
- **Pull request:** pending creation

## Key changes

- Renamed backend settings, environment variables, Lambda startup secret loading, and controlled configuration errors to OpenRouter terminology.
- Kept the official `openai` Python SDK and Responses API workflow, constructing its client with the OpenRouter endpoint. The original `provider.require_parameters=true` routing constraint was later removed by Task 018 after production verification identified it as incompatible.
- Set the default model to `openai/gpt-5.6-luna`.
- Updated Terraform to read only `/opspilot/prod/openrouter-api-key` with `ssm:GetParameter`, and to configure the renamed Lambda environment variables.
- Updated provider-boundary and runtime-secret tests, plus the frontend error-message regression assertion. No frontend application behavior or API contract changed.

## Verification

- `python -m ruff check app tests` — passed.
- `python -m mypy app` — passed: 23 source files, no issues.
- `python -m pytest` — passed: 37 tests.
- `python -m compileall -q app tests` — passed.
- `terraform fmt -check main.tf` — passed.
- `terraform validate` — passed.
- `npm run test -- --run` — passed: 18 tests.
- `npm run typecheck` — passed.

## Known limitations and decisions

- This task itself did not change AWS resources, SSM values, or deployment. Subsequent Task 020 controlled deployment and verification confirmed the production provider/router is OpenRouter; Task 021 is documentation-only closeout.
- No provider abstraction, fallback key, optional OpenRouter attribution headers, or upstream-provider pin was added.

## Recommended next task

Review and merge the Task 010 pull request, then plan a separately controlled deployment and smoke-test task.
