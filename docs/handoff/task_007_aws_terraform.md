# Task 007 — AWS and Terraform

## Goal

Prepare the fixed, small AWS deployment architecture for OpsPilot without creating cloud resources during this implementation pass.

## Git context

- **Branch:** `task/007-aws-terraform`
- **Base commit:** `aab192f35afca004630a72aa913b01157f2b5434`
- **PR:** [#8](https://github.com/yi0805/opspilot/pull/8) — `Task 007: add AWS Terraform deployment`.
- **Final verified head:** The PR branch contains the Task 007 implementation and subsequent review corrections; the final verified head SHA is reported in the completion report.

## Architecture decision

CloudFront is the intended public application entry point. Its default origin is a private S3 bucket holding the React/Vite build, while its `/api/*` behavior forwards requests to the App Runner FastAPI service over HTTPS. This provides same-origin frontend API calls. App Runner loads a private ECR image, reads `OPENAI_API_KEY` from the exact SSM SecureString `/opspilot/prod/openai-api-key`, and uses deterministic seeded SQLite data at `/tmp/opspilot.db`. App Runner's standard service URL remains directly internet-accessible by design; private ingress is intentionally not used because it would add VPC/PrivateLink infrastructure and cost.

This preserves same-origin frontend API calls and avoids production CORS complexity. It intentionally excludes a VPC, RDS, API Gateway, Lambda, ECS, load balancer, remote state, custom domain, and CI/CD deployment workflow.

## Key changes

- Added `backend/Dockerfile` and `.dockerignore` for a Python 3.12 production image. The container runs the idempotent seed command before one Uvicorn process bound to port 8080.
- Added a small Terraform root at `infra/terraform/` for immutable, force-deletable ECR, narrowly scoped App Runner ECR/instance roles, SSM parameter reference, one-instance App Runner, private S3 with CloudFront Origin Access Control, and one CloudFront distribution.
- Configured CloudFront `/api/*` as HTTPS-only App Runner routing with POST support, no caching, forwarded request data except the viewer `Host` header, and a 120-second origin read timeout.
- Configured S3 public-access blocking, bucket-owner-enforced object ownership, SSE-S3, and a distribution-scoped read-only bucket policy.
- Added local Terraform state and variable-input ignore rules without ignoring `.terraform.lock.hcl`.
- Updated README deployment instructions and marked the roadmap task **In Progress**.

## Local verification

- `terraform fmt -recursive` and `terraform fmt -check -recursive`: passed.
- `terraform init -backend=false`: passed and selected `hashicorp/aws` v6.64.0; `.terraform.lock.hcl` was generated for commit.
- `terraform validate`: passed.
- `docker build --tag opspilot-backend:task007-smoke backend`: passed.
- Production-configured local container smoke test: seed completed, `GET /api/health` returned `200 {"status":"ok"}`, and a no-key agent request returned the expected controlled `503`; no live OpenAI call occurred.
- Backend quality checks: Ruff, mypy, pytest (33 passed), and compileall passed.
- Frontend quality checks: `npm ci`, tests (18 passed), lint, typecheck, and build passed.
- No Terraform plan was run because `aws sts get-caller-identity` reported that local AWS credentials are not configured.

## Deployment status and known limitations

- **Implemented locally:** Dockerfile, Terraform configuration, deployment documentation, and local-state ignore rules.
- **Validated locally:** Terraform format/init/validate, Docker build/runtime smoke test, and all existing backend/frontend quality checks passed.
- **NOT YET deployed:** no Terraform apply, Docker ECR push, S3 sync, SSM parameter write, CloudFront invalidation, or other AWS mutation was performed in this pass.
- Terraform deliberately does not create or store the OpenAI key. The SecureString value must be created outside Terraform before the full apply.
- The App Runner service has a minimum of one instance and therefore has ongoing runtime cost until destroyed; it is capped at one instance and 10 concurrent requests.
- SQLite data is ephemeral by design, safe only because it is deterministic synthetic read-only demo data.
- The deployment has no authentication and App Runner/API ingress is public. Successful agent requests consume OpenAI API usage, so configure provider billing and usage controls before making this controlled portfolio/demo deployment public, and destroy it when not needed.
- S3 objects require manual removal before destroy because the bucket intentionally uses `force_destroy = false`; the Terraform-managed ECR repository uses `force_delete = true`; the externally created SSM SecureString remains unless manually deleted.

## Recommended next task / exact next verification step

Review this local commit. After approval, create the SSM SecureString, perform the documented targeted ECR bootstrap with the real immutable commit-SHA image tag, push that image, run the full Terraform apply, upload frontend assets, and smoke-test `GET /api/health` through the generated CloudFront URL. Task 007 remains **In Progress** until those deployment checks succeed.
