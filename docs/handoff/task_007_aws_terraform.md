# Task 007 — AWS and Terraform

## Goal

Prepare a small AWS deployment for OpsPilot without creating cloud resources during this local migration pass.

## Git context

- **Branch:** `task/007-aws-terraform`
- **Base commit:** `aab192f35afca004630a72aa913b01157f2b5434`
- **PR:** [#8](https://github.com/yi0805/opspilot/pull/8) — `Task 007: add AWS Terraform deployment`.
- **Final verified head:** The PR branch contains the implementation and subsequent review corrections; the final verified head SHA is reported in the completion report.

## Architecture decision

The original App Runner design was replaced because App Runner is unavailable while this AWS account remains on its Free plan. CloudFront remains the intended application entry point: its default origin is the private S3 React/Vite build and `/api/*` is routed over HTTPS to a public Lambda Function URL. Lambda runs the FastAPI application through Mangum from a private ECR image.

The Function URL uses public `NONE` authorization by design. It remains directly internet-accessible; private ingress would require additional VPC/PrivateLink infrastructure and cost. The frontend keeps its same-origin `/api/...` requests and needs no production CORS configuration.

## Key changes

- Replaced App Runner resources, IAM roles, outputs, and CloudFront origin with a Lambda container-image function, Function URL, two public Function URL permissions, execution role, ECR retrieval policy, and seven-day CloudWatch log group.
- Added a Python 3.12 Lambda image, Mangum handler, and a cold-start-only SSM SecureString loader. The loader reads `/opspilot/prod/openai-api-key` only when `OPENAI_API_KEY` is absent, then seeds deterministic SQLite before importing FastAPI.
- Preserved immutable, scan-on-push, force-deletable ECR; private S3/OAC; no API caching; and CloudFront's 120-second API origin timeout.
- Restricted Lambda to 512 MB, a 110-second timeout, x86_64 image execution, and reserved concurrency of one.

## Local verification

- Terraform format, initialization with local state, and validation passed. A read-only plan through the `opspilot` profile returned `20 to add, 0 to change, 0 to destroy` and contained only the intended architecture.
- The Lambda image was built and invoked locally through the Lambda Runtime Interface Emulator using a dummy key; `GET /api/health` returned `statusCode: 200` with `{"status":"ok"}` without contacting SSM or OpenAI.
- Backend quality checks passed: Ruff, mypy, compileall, and 36 pytest tests. Frontend `npm ci`, tests (18), lint, typecheck, and production build passed.
- The read-only AWS identity, Lambda list, and ECR list checks succeeded through the `opspilot` profile; no AWS resource was created, updated, or deleted in this pass.

## Deployment status and limitations

- **Implemented locally:** Lambda deployment code, image packaging, runtime secret boundary, tests, documentation, and local-state configuration.
- **NOT YET deployed:** no Terraform apply, ECR push, SSM write, S3 sync, CloudFront invalidation, or other AWS mutation has occurred.
- The OpenAI key remains outside Terraform state in an externally managed SecureString.
- The Lambda Function URL/API has no authentication. Successful public agent requests consume OpenAI API usage. Reserved concurrency of one limits simultaneous function executions but does not cap total OpenAI usage over time; provider billing and usage controls still matter.
- The deployment is intended as a controlled portfolio/demo environment designed to stay within available Free-plan services/allowances for small demo usage, not as a guarantee of zero cost. Destroy it when it is not needed.
- S3 frontend objects must be manually removed before destroy because `force_destroy = false`. Terraform destroys the Lambda, Function URL, permissions, CloudFront, ECR, and other managed infrastructure; ECR uses `force_delete = true`. The external SSM parameter remains unless deliberately deleted manually.

## Recommended next verification step

After review, authenticate the named profile with `aws login --profile opspilot --region ap-southeast-2` if needed, then set `$env:AWS_PROFILE = "opspilot"`, `$env:AWS_REGION = "ap-southeast-2"`, and `$region = $env:AWS_REGION` so AWS CLI and Terraform use the same temporary credential context. Temporary credentials can expire and require `aws login` again. Initialize and plan, create/update the external SSM SecureString, bootstrap only ECR and its Lambda retrieval policy, push the immutable current Git-SHA Lambda image, then run a normal plan/apply. Build and sync the frontend, invalidate CloudFront, verify direct Function URL and CloudFront health, verify the frontend, make one controlled live agent request through CloudFront, and document that verified deployment. Task 007 remains **In Progress** until those checks succeed.
