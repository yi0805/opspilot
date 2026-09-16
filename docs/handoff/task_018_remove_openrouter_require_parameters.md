# Task 018 — Remove Incompatible OpenRouter `require_parameters` Routing Constraint

## Status

Complete as a repository-only change; not deployed.

## Goal

Remove the incompatible OpenRouter `provider.require_parameters` routing constraint from the reasoning and final Responses API calls without changing agent behavior.

## Git context

- **Branch:** `task/018-remove-openrouter-require-parameters`
- **Base commit:** `c17ba45ee2e157d722681c2f0582a2a33943632a`
- **Final commit:** this handoff's containing commit
- **Pull request:** pending creation

## Key changes

- Removed `extra_body={"provider": {"require_parameters": True}}` from both `_create_reasoning_response` and `_create_final_response`.
- Added request assertions that every local fake-client request omits `extra_body`, `provider`, and `require_parameters`.
- Preserved the model, OpenRouter client configuration, system instructions, tools, sequential tool execution, final `tool_choice="none"`, and structured final-output schema.

## Verification

- `python -m ruff check app tests` — passed.
- `python -m mypy app` — passed: 23 source files, no issues.
- `python -m pytest` — passed: 40 tests. Only existing third-party deprecation warnings were reported.
- `python -m compileall -q app tests` — passed.
- `git diff --check` — passed.

## Known limitations and decisions

- No provider or model request was made. Tests use local fake clients only.
- No AWS, Terraform, SSM, deployment, secret retrieval, Docker build, or production smoke test was performed.
- No replacement provider routing configuration was added; OpenRouter performs normal provider routing.

## Recommended next task

Review the Task 018 pull request and verify the change in the separately authorized deployment workflow.
