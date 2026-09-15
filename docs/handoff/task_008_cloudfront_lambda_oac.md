# Task 008 — CloudFront-Only Lambda Origin Access

## Status

**COMPLETE — READY FOR CHATGPT REVIEW**

## Goal

Remove direct unauthenticated access to the Lambda Function URL while preserving the existing CloudFront `/api/*` application path.

## Git context

- **Branch:** `task/008-cloudfront-lambda-oac`
- **Base commit:** `356c5bfa5e7d2ab60f45b12bfded1ce2da3c6687`
- **Final implementation commit:** recorded by the Task 008 branch and pull request after this handoff is committed.
- **Pull request:** pending creation; this task does not merge it.

## Security problem addressed

Task 007 exposed the Lambda Function URL with `NONE` authentication and wildcard resource-policy permissions. The Task 008 Terraform configuration changes the URL to `AWS_IAM` and authorizes only CloudFront service requests from the application distribution.

## Final code design

- The Lambda Function URL keeps buffered invocation and changes authorization from `NONE` to `AWS_IAM`.
- A dedicated Lambda-origin CloudFront Origin Access Control signs every origin request with SigV4. The existing S3 OAC remains unchanged.
- The Lambda origin uses that dedicated OAC.
- The two wildcard Lambda permissions are replaced by `cloudfront.amazonaws.com` permissions scoped with the CloudFront distribution ARN: one for `lambda:InvokeFunctionUrl` with `AWS_IAM`, and one for `lambda:InvokeFunction` constrained to invocation through the Function URL.
- Lambda permissions depend on the CloudFront distribution ARN, while the distribution depends only on the Lambda URL and OAC. This one-way relationship avoids a Terraform dependency cycle.

## POST payload hash requirement

CloudFront Lambda Function URL OAC requires `x-amz-content-sha256` for POST/PUT request bodies. The frontend serializes the request once with `JSON.stringify({ question })`, encodes that exact string with `TextEncoder`, uses browser `crypto.subtle.digest('SHA-256', ...)`, converts the digest to lowercase hexadecimal, and sends it in the required header. No third-party crypto dependency was added.

## Verification

The frontend test setup supplies Node's standard Web Crypto implementation only when jsdom does not provide `crypto.subtle`. The request test verifies the unchanged endpoint and JSON body, `Content-Type`, and the known SHA-256 digest for the exact serialized body. Existing component tests cover successful responses plus network, HTTP, unreadable-response, and invalid-shape handling.

All local quality checks passed:

```text
terraform fmt -check: passed
terraform validate: Success! The configuration is valid.
backend> python -m pytest: 36 passed (one existing pytest deprecation warning)
backend> python -m ruff check app tests: All checks passed
backend> python -m mypy app: Success: no issues found in 23 source files
backend> python -m compileall -q app tests: passed
frontend> npm ci: passed
frontend> npm test -- --run: 18 passed
frontend> npm run lint: passed
frontend> npm run typecheck: passed
frontend> npm run build: passed
```

No read-only plan was run because the workstation initially had no Terraform executable; a temporary Terraform 1.9.8 CLI was used for local formatting and validation only. It did not run a plan or contact AWS.

## Deployment status and expected verification

No AWS deployment, Terraform apply/destroy, state mutation, service invocation, Docker activity, or frontend deployment was performed for this task. After a reviewed deployment, verify:

- CloudFront `GET /api/health` succeeds.
- CloudFront `POST /api/agent/query` succeeds.
- A direct unsigned Lambda Function URL request returns HTTP 403.

## Known limitations

- Deployment verification remains pending; the live Task 007 Function URL is unchanged until Terraform is applied.
- The Lambda backend, synthetic data, OpenAI usage, and other Task 007 operational limitations are unchanged.

## Recommended next task

Review and deploy Task 008 through the normal controlled Terraform workflow, then record the post-deployment verification separately.
