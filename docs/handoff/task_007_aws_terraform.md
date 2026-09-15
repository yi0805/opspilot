# Task 007 — AWS and Terraform Handoff

## Status

**COMPLETE**

## Goal

Deploy a small, cost-conscious, verified AWS version of OpsPilot using Terraform, with an external secret boundary and documented production smoke checks.

## Git context

- **Branch:** `task/007-aws-terraform`
- **Base commit:** `aab192f35afca004630a72aa913b01157f2b5434`
- **Implementation artifact commit:** `992490a6220fe6b4ef3e27b4ebc68b9e8914bc93`
- **PR:** [#8](https://github.com/yi0805/opspilot/pull/8) — `Task 007: add AWS Terraform deployment`

The deployed backend image intentionally remains tied to the implementation artifact commit above; a later documentation-only commit must not trigger a rebuild or redeploy.

## Final architecture and deployed resources

Browser traffic enters CloudFront distribution `E3CZ1JJRB8PXIP` at <https://d10nfs9ms4ms1h.cloudfront.net>. The default `/*` behavior serves the React/Vite frontend from private bucket `opspilot-frontend-90fcbd693161f5fc27cac696f8`; `/api/*` forwards to the public Lambda Function URL, then the Lambda container, Mangum, FastAPI, and OpenAI Responses API.

- Lambda function: `opspilot-backend`, image package, x86_64, 512 MB, 110-second timeout.
- Lambda Function URL: public, `NONE` authorization, buffered invoke mode.
- ECR: `opspilot-backend`, immutable tags, scan on push, lifecycle retention of five images, and a known-good Lambda retrieval policy.
- SSM: `/opspilot/prod/openai-api-key` is an externally managed SecureString and is outside Terraform state.
- Frontend bucket: private, BucketOwnerEnforced, public access blocked, AES256 encryption, and CloudFront-only read policy.
- No per-function reserved concurrency is configured. The account concurrency quota is 10, all currently unreserved; AWS requires unreserved capacity to remain available.

## Deployed artifact and frontend

- Backend image tag: `992490a6220fe6b4ef3e27b4ebc68b9e8914bc93`
- Backend image digest: `sha256:b9fb97ec1431b31242b8a452070285c127a57856c5d6e14e7d6c8a4b2c2f889e`
- Frontend deployment: 3 files, 234,991 bytes.
- CloudFront invalidation: `I2B19UQY6PHETREMQSMKLBL79R`, completed.

Lambda container builds must use a Lambda-compatible single-platform image rather than an OCI image index with provenance artifacts:

```powershell
docker buildx build `
  --platform linux/amd64 `
  --provenance=false `
  --sbom=false `
  --load `
  --tag "opspilot-backend:$imageTag" `
  ../../backend
```

App Runner was abandoned because it was unavailable on the target AWS Free-plan account.

## Verification

Terraform applied successfully. The authorized tainted Lambda replacement recovery ended with `6 added, 0 changed, 1 destroyed`; the only destroy was that expected replacement. The final infrastructure plan before frontend deployment was clean. A later plan was not rerun during smoke testing because Terraform CLI was unavailable in that environment; frontend S3 uploads and CloudFront invalidations are intentionally outside Terraform.

- Direct Lambda Function URL `GET /api/health`: HTTP 200, `{"status":"ok"}`.
- CloudFront `GET /api/health`: HTTP 200, `{"status":"ok"}`.
- CloudFront frontend `GET /`: HTTP 200, HTML, OpsPilot page, and JS/CSS assets verified.
- Exactly one controlled external `POST /api/agent/query` completed with HTTP 200 and status `completed` in about 21.3 seconds.
- That request compared FW-100 sales and inventory using `query_sales` and `query_inventory`: recent sales 310, on hand 28, reserved 6, available 22, inbound 120, reorder point 30. It correctly identified replenishment risk and recommended verifying or expediting inbound delivery while continuing replenishment.
- CloudWatch showed no initialization, SSM configuration, request, timeout, or unhandled-exception errors; no secrets were exposed.

## Limitations and operational notes

- The Function URL/API is directly internet-accessible and unauthenticated by design.
- Successful agent requests consume OpenAI usage; Lambda, ECR, S3, and CloudFront can also incur charges. This is not a guaranteed zero-cost deployment.
- No persistent production database exists; seeded SQLite under Lambda `/tmp` is ephemeral.
- No custom domain, VPC/private ingress, API Gateway, or CI/CD deployment pipeline is provisioned.
- The S3 bucket uses `force_destroy = false`, so frontend objects must be removed before Terraform destroy. The external SSM SecureString remains unless manually removed.

## Recommended next task

Proceed to the next roadmap task only when separately authorized. Do not rebuild or redeploy Task 007 merely for documentation changes.
