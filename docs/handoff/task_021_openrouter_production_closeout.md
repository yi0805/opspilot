# Task 021 — OpenRouter Production Verification Closeout

## Status

Complete — documentation-only closeout of the controlled deployment and final production verification completed by Task 020.

## Goal

Record the final, production-verified OpenRouter architecture and migration status without changing runtime code, tests, Terraform, AWS resources, secrets, images, or deployment state.

## Git context

- **Branch:** `task/021-openrouter-production-closeout`
- **Base commit:** `f1b397c1d32208df885fd7a36dbf73c504c1f390`
- **Final commit:** this handoff's containing commit
- **Pull request:** #15

## Key changes

- Updated repository documentation to identify OpenRouter as the production AI provider/router, using the official OpenAI Python SDK with OpenRouter's base URL and model `openai/gpt-5.6-luna`.
- Recorded that OpenRouter uses normal provider routing: `provider.require_parameters` is intentionally absent from reasoning and final Responses API calls because it caused the verified 404 routing failure.
- Recorded that the sequential allowlisted tool workflow, `parallel_tool_calls=False`, final structured output, and application-owned authoritative evidence remain unchanged.
- Recorded the production CloudFront/Lambda security posture: CloudFront remains healthy; the Function URL remains `AWS_IAM` with buffered invocation; CloudFront OAC remains SigV4 `signing=always`; unsigned direct Function URL access is denied; and Lambda retains only the exact `ssm:GetParameter` access required for `/opspilot/prod/openrouter-api-key`.

## Task 020 production verification recorded

- Task 020 deployed the Task 018 routing fix successfully in Lambda image `f1b397c1d32208df885fd7a36dbf73c504c1f390`.
- CloudFront and `GET /api/health` returned HTTP 200.
- A production agent request returned HTTP 200 with application status `completed`.
- `query_sales` and `query_inventory` evidence completed successfully, each with source `synthetic_business_data`.
- The returned recommendation passed the supporting-evidence guardrail.
- No provider-failure warning occurred.
- The final Terraform plan reported no changes.

## Verification

- Documentation review is limited to the checked-in architecture, deployment, roadmap, and Task 010, Task 014, and Task 018 handoffs.
- No live provider request, AWS access, secret retrieval, image build/push, deployment, or Terraform mutation is part of this task.

## Known limitations and decisions

- The prior OpenAI SecureString and previous ECR images are intentionally retained temporarily as rollback material.
- Rollback-material cleanup is deferred to a separately reviewed task; this task does not claim or perform deletion.

## Recommended next task

Plan and review rollback-material cleanup separately after confirming its retention window and recovery requirements.
