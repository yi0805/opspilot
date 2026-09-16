# Task 022 — Rollback Material Cleanup Assessment

## Status

Complete — read-only assessment and documentation only. Cleanup remains a separate, explicitly authorized task.

## Goal

Assess the rollback material retained after the OpenRouter migration and recommend a minimal, safe future cleanup scope without retrieving secret values or changing AWS, Terraform, runtime, frontend, or deployment state.

## Git context

- **Branch:** `task/022-rollback-cleanup-assessment`
- **Base commit:** `eecbd5d88665f16e01e8fe177eba1bb0c2a0c24a`
- **Final commit:** this handoff's containing commit
- **Pull request:** #16

## Read-only AWS inspection

All commands used AWS profile `opspilot` in `ap-southeast-2`. No secret value was requested, decrypted, printed, or retained.

### Current Lambda

- Lambda `opspilot-backend` exists, has `State=Active`, `LastUpdateStatus=Successful`, and was last modified at `2026-09-16T10:17:27Z`.
- It is an image-package Lambda. Its configured image is `055408888083.dkr.ecr.ap-southeast-2.amazonaws.com/opspilot-backend:f1b397c1d32208df885fd7a36dbf73c504c1f390`, resolved to digest `sha256:0da58199ff2ca350fae9ec3a2a56598ce0db7f0cb7fa3e3c6d9e5cab2749886a`.
- Environment variable names are `APP_ENV`, `DATABASE_URL`, `OPENROUTER_MODEL`, and `OPENROUTER_SSM_PARAMETER_NAME`. The two non-secret OpenRouter configuration values identify model `openai/gpt-5.6-luna` and parameter name `/opspilot/prod/openrouter-api-key`.
- The execution role is `arn:aws:iam::055408888083:role/opspilot-lambda-execution`.
- The role has one inline policy and no attached managed policies or permissions boundary. Its only SSM permission is `ssm:GetParameter` for `arn:aws:ssm:ap-southeast-2:055408888083:parameter/opspilot/prod/openrouter-api-key`; it neither references nor permits the legacy OpenAI parameter.

### SSM parameters

`aws ssm describe-parameters` was used for metadata only. It does not return parameter values, and `--with-decryption` was not used.

| Parameter | Type | Version | Last modified | Classification |
| --- | --- | ---: | --- | --- |
| `/opspilot/prod/openrouter-api-key` | SecureString | 1 | 2026-09-16T17:18:51+12:00 | REQUIRED / DO NOT DELETE |
| `/opspilot/prod/openai-api-key` | SecureString | 1 | 2026-09-15T07:48:02+12:00 | KEEP TEMPORARILY |

The OpenRouter parameter is required by the current Lambda environment, runtime secret loader, Terraform IAM policy, and production deployment. The OpenAI parameter is not reachable by the current Lambda role and is not referenced by current code or Terraform. It retains limited, paired rollback value only while the direct-OpenAI image below is intentionally retained.

### ECR inventory

Repository `opspilot-backend` has immutable tags and a lifecycle policy configured to retain only the five most recent image records. The following metadata was observed; no image was deleted.

| Tags | Digest | Pushed (NZDT) | Size (bytes) | Assessment |
| --- | --- | --- | ---: | --- |
| `3a94f43cf083c752d046aca28225e80d21723b35` | `sha256:ae4b4f1c60364db46584a8145d1e04140e09dcad7399d86dcf42fb9c60424ca6` | 2026-09-15 08:25:58 | 220,028,199 | SAFE CANDIDATE FOR LATER DELETION |
| untagged, linked from `3a94f43…` | `sha256:381f63220df27a9cd315267459f3ede4c6926ba7ae04d47d180c39fdafe22942` | 2026-09-15 08:25:57 | 220,028,199 | SAFE CANDIDATE FOR LATER DELETION |
| untagged, linked from `3a94f43…` | `sha256:bc848db3a5131cbf812d447762dcc82fd3c286381db49cdf0f8bf4a74dcd7f4f` | 2026-09-15 08:25:57 | 1,740 | SAFE CANDIDATE FOR LATER DELETION |
| `2005cd8ff4d9d94de3e891e056f5c2dda930f8d8`, `992490a6220fe6b4ef3e27b4ebc68b9e8914bc93` | `sha256:b9fb97ec1431b31242b8a452070285c127a57856c5d6e14e7d6c8a4b2c2f889e` | 2026-09-15 08:46:04 | 220,028,199 | KEEP TEMPORARILY |
| `af79175d8827cffdbab1bbf569d29e6d237ce3d3` | `sha256:e730ad5ab49cabb0392c8200d2d108ceaa381f358927fd72d245ccaff51af95e` | 2026-09-16 17:26:14 | 220,087,967 | SAFE CANDIDATE FOR LATER DELETION |
| `c17ba45ee2e157d722681c2f0582a2a33943632a` | `sha256:ccf0be3c1868763bbd4b5bb6d6071be57f5f7e9b1811846348fe67bec1718702` | 2026-09-16 18:00:23 | 220,089,196 | SAFE CANDIDATE FOR LATER DELETION |
| `f1b397c1d32208df885fd7a36dbf73c504c1f390` | `sha256:0da58199ff2ca350fae9ec3a2a56598ce0db7f0cb7fa3e3c6d9e5cab2749886a` | 2026-09-16 22:10:37 | 220,088,980 | REQUIRED / DO NOT DELETE |

The tagged `3a94f43…` record is an OCI image index. Metadata-only manifest inspection showed that it references both listed untagged records, so those three records must be considered one cleanup group rather than unrelated untagged images.

The `2005cd8…` and `992490a…` tags resolve to the same pre-migration direct-OpenAI image. Task 007 recorded its digest as the deployed backend artifact, and the corresponding historical code uses `OPENAI_API_KEY` and `OPENAI_SSM_PARAMETER_NAME`; it is the one known previous OpenAI rollback image worth retaining temporarily. The duplicate tags do not create a second image.

`af79175…` is the initial OpenRouter migration image, and `c17ba45…` is the subsequent observability image. Historical source inspection confirms both contain `provider.require_parameters=true`; Task 018 removed that constraint after it caused the verified OpenRouter routing failure. Neither is the verified working OpenRouter rollback artifact and neither is an active production dependency.

## Repository and infrastructure evidence

- Current Terraform names only `/opspilot/prod/openrouter-api-key`, grants the Lambda role only that parameter's ARN, and sets `OPENROUTER_MODEL` plus `OPENROUTER_SSM_PARAMETER_NAME`.
- Current Lambda runtime calls only `ensure_openrouter_api_key()` and reads the parameter named by `OPENROUTER_SSM_PARAMETER_NAME`.
- Current source, Terraform, and Lambda configuration contain no active `OPENAI_API_KEY`, `OPENAI_SSM_PARAMETER_NAME`, `/opspilot/prod/openai-api-key`, `af79175…`, or `c17ba45…` production dependency. Historical handoffs mention old identifiers only as historical records.
- Current deployment references only tag `f1b397…` and digest `sha256:0da…`.

## Retention and recovery recommendation

Use a simple 30-day intended rollback-retention window starting from the 2026-09-16 successful OpenRouter production verification:

1. Retain the current OpenRouter secret and image at all times.
2. During the window, retain exactly one previous known-good direct-OpenAI image (`sha256:b9fb…`, with either existing tag) and `/opspilot/prod/openai-api-key`. Multiple OpenAI-era images do not add meaningful recovery value.
3. The old OpenAI secret has only limited rollback value: it is useful solely with that retained image and an approved infrastructure/configuration rollback. An old image alone cannot work because current Lambda configuration names and the execution-role permission target the OpenRouter parameter only.
4. If OpenRouter unexpectedly fails, recover through a separately reviewed rollback that restores the historical OpenAI Terraform/runtime configuration, changes the Lambda image tag to the retained direct-OpenAI image, restores `OPENAI_MODEL` and `OPENAI_SSM_PARAMETER_NAME`, restores role access to the legacy parameter, applies the infrastructure change, and then performs the appropriate controlled verification. Retaining the current Git history or a reviewed rollback commit is therefore also necessary.

The 30-day period is a retention target, not a guarantee that the direct-OpenAI image will remain physically available for all 30 days. The current ECR lifecycle configuration is count-based (`tagStatus="any"`, `countType="imageCountMoreThan"`, `countNumber=5`), so additional backend image pushes during that period may make the retained rollback image eligible for expiration. Before any additional backend image push during the intended retention window, re-evaluate the rollback-image retention decision. If guaranteed 30-day image retention is required, changing or protecting the ECR lifecycle behavior must be performed in a separate reviewed and authorized task; Task 022 does not change that policy.

At the end of the window, if no rollback is needed, a separate authorized cleanup task should delete the following exact scope after re-listing metadata immediately before mutation:

- `/opspilot/prod/openai-api-key`;
- the direct-OpenAI image digest `sha256:b9fb97ec1431b31242b8a452070285c127a57856c5d6e14e7d6c8a4b2c2f889e` and both of its tags (`2005cd8…`, `992490a…`);
- obsolete migration-era image digests `sha256:e730ad5ab49cabb0392c8200d2d108ceaa381f358927fd72d245ccaff51af95e` (`af79175…`) and `sha256:ccf0be3c1868763bbd4b5bb6d6071be57f5f7e9b1811846348fe67bec1718702` (`c17ba45…`); and
- the obsolete OCI-index group `sha256:ae4b4f1c60364db46584a8145d1e04140e09dcad7399d86dcf42fb9c60424ca6` (`3a94f43…`) with linked untagged manifests `sha256:381f63220df27a9cd315267459f3ede4c6926ba7ae04d47d180c39fdafe22942` and `sha256:bc848db3a5131cbf812d447762dcc82fd3c286381db49cdf0f8bf4a74dcd7f4f`.

That future task must retain `/opspilot/prod/openrouter-api-key` and `sha256:0da58199ff2ca350fae9ec3a2a56598ce0db7f0cb7fa3e3c6d9e5cab2749886a` (`f1b397…`). Immediately before deleting anything, it must re-validate ECR inventory and lifecycle effects, as well as the Lambda resolved image, SSM/IAM references, ECR image-index linkage, and retention-window decision.

## Verification

- Confirmed the requested starting branch, exact base SHA, and clean working tree before creating this branch.
- Performed only read-only AWS Lambda, SSM metadata, IAM metadata/policy, and ECR metadata/manifest inspection.
- Did not retrieve/decrypt either SSM parameter, print any API key, invoke OpenRouter/OpenAI, build/push images, deploy, change Lambda/IAM, apply Terraform, or delete AWS resources.
- Ran `git diff --check` after documentation changes.
- Reviewed the final diff and confirmed it contains documentation only (`ROADMAP.md` and this handoff).

## Known limitations and decisions

- No live rollback was attempted; the OpenAI rollback image is described as previously known-good from Task 007 evidence, not re-validated by this read-only assessment.
- AWS's current lifecycle policy counts all image records and may expire images asynchronously. It should not replace a deliberate, reviewed cleanup decision while rollback material is intentionally retained.
- Cleanup requires a separate authorized task. This task made no deletion or other AWS mutation.

## Recommended next task

After the 30-day retention window, perform a separately authorized, re-validated cleanup of the listed obsolete SSM and ECR resources.
