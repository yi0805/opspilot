# Task 008 — CloudFront-Only Lambda Origin Access

## Status

**COMPLETE — IMPLEMENTATION, CONTROLLED DEPLOYMENT, AND PRODUCTION VERIFICATION RECORDED**

## Goal

Remove direct unauthenticated access to the Lambda Function URL while preserving the existing CloudFront `/api/*` application path.

## Git context

- **Branch:** `task/008-cloudfront-lambda-oac`
- **Base commit:** `356c5bfa5e7d2ab60f45b12bfded1ce2da3c6687`
- **Initial implementation commit reviewed by ChatGPT:** `80923b1658a12a811fe07d9885d163a83aa8263d`
- **Verified deployment preparation commit:** `35498f3d62ab4df78a668e02a916a0a73bb77a0a`
- **Pull request:** [#9 — Task 008: restrict Lambda origin to CloudFront](https://github.com/yi0805/opspilot/pull/9)

## Security problem addressed

Task 007 exposed the Lambda Function URL with `NONE` authentication and wildcard resource-policy permissions. Task 008 changed the URL to `AWS_IAM` and authorizes only CloudFront service requests from the application distribution.

## Final code design

- The Lambda Function URL keeps buffered invocation and now uses `AWS_IAM` authorization.
- Dedicated Lambda-origin OAC `E32M33I13ENXOW` signs every origin request with SigV4. The existing S3 OAC remains unchanged.
- The Lambda origin uses that dedicated OAC.
- The two wildcard Lambda permissions are replaced by `cloudfront.amazonaws.com` permissions scoped with the CloudFront distribution ARN: one for `lambda:InvokeFunctionUrl` with `AWS_IAM`, and one for `lambda:InvokeFunction` constrained to invocation through the Function URL.
- Lambda permissions depend on the CloudFront distribution ARN, while the distribution depends only on the Lambda URL and OAC. This one-way relationship avoids a Terraform dependency cycle.

## Deployment sequencing

AWS requires CloudFront permission to exist before enabling the Lambda OAC on the CloudFront distribution. The Terraform resources deliberately retain the one-way deployment relationship from the CloudFront distribution to the Lambda permission resources: the permissions reference the distribution ARN, while the distribution has no dependency on those permission resources. This avoids a Terraform graph cycle, but does not enforce the required operational ordering. The controlled deployment therefore updated the frontend first, switched the Function URL to `AWS_IAM`, manually added and imported the two CloudFront permissions, applied only the Lambda OAC and distribution change, verified CloudFront, then removed the Terraform-managed legacy permissions.

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

## Controlled deployment and security verification

Deployment used AWS account `055408888083`, profile `opspilot`, and region `ap-southeast-2`. Terraform CLI `1.9.8` reviewed an initial plan of `3 add, 3 change, 2 destroy`; the changes were expected. The rebuilt frontend passed 18 tests, lint, typecheck, and build, then deployed to `opspilot-frontend-90fcbd693161f5fc27cac696f8`. CloudFront invalidation `IC3U2HWVGFYEU6WGF7447MK65Y` completed.

The final production state is CloudFront distribution `E3CZ1JJRB8PXIP` (`Deployed`) at `https://d10nfs9ms4ms1h.cloudfront.net`, with Lambda-origin OAC `E32M33I13ENXOW`. The Function URL uses `AWS_IAM`; `AllowCloudFrontFunctionUrl` permits `cloudfront.amazonaws.com` to call `lambda:InvokeFunctionUrl` only with the `AWS_IAM` condition and distribution SourceArn, while `AllowCloudFrontInvocationThroughFunctionUrl` permits `lambda:InvokeFunction` only through the Function URL and from that same SourceArn.

The two old AWS-created wildcard statements, `FunctionURLAllowPublicAccess` and `FunctionURLAllowInvokeAction`, were outside the current Terraform-managed permission resources. After validating that both belonged to the former public Function URL configuration, they were removed manually. No wildcard Function URL principal remains.

CloudFront `GET /` and `GET /api/health` returned HTTP 200; the health payload was `{"status":"ok"}`. Direct unsigned Function URL `GET /api/health` and invalid-body `POST /api/agent/query` both returned HTTP 403. Exactly one controlled CloudFront agent request completed successfully (HTTP 200, `completed`, approximately 21.465 seconds) with `query_sales` and `query_inventory` evidence. The final Terraform plan reported `No changes`.

CloudWatch inspection of 21 recent events found no initialization, SSM, unhandled-exception, timeout, or secret-exposure indicators. No secret was exposed.

## Known limitations

- The Lambda backend, synthetic data, OpenAI usage, and other Task 007 operational limitations are unchanged.

## Recommended next task

Review PR #9 and its CI before deciding whether to merge; no additional live agent request is required for Task 008 verification.
