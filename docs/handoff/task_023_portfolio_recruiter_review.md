# Task 023 — Portfolio Demo & Recruiter Review

## Status

Complete — documentation-only recruiter-facing review. No application, infrastructure, deployment, or cloud resource changes were made.

## Goal and review scope

Review OpsPilot as a technical recruiter or junior software, cloud, or AI engineering hiring manager would encounter it for the first time. The review covered the README, roadmap, repository structure, GitHub Actions workflow, current screenshots, Terraform and deployment documentation, and the checked-in agent implementation needed to validate recruiter-facing claims.

## Git context

- **Branch:** `task/023-portfolio-recruiter-review`
- **Base commit:** `efd75a146d2f801746922c9304ea920bfd088ffb`
- **Final commit:** this handoff's containing commit
- **Pull request:** pending creation, if GitHub authentication permits

## Recruiter-facing findings

### Already strong

- The opening description identifies OpsPilot as an AI business-operations agent and clearly states that its data is synthetic.
- A live demo and two screenshots are near the top of the README. The completed-analysis screenshot visibly connects an answer and recommendation to sales and inventory evidence; the workspace screenshot shows the initial question experience and representative prompts.
- The detailed documentation accurately explains the controlled, sequential, allowlisted tool workflow; the model's lack of direct database access; application-owned evidence; the supporting-evidence recommendation guardrail; provider and model configuration; and the AWS deployment security posture.
- The architecture diagram, deployment material, local quality commands, and CI workflow make the project technically credible for a reviewer who reads further.

### Weakness found

The first screen did not provide a single compact scan of what the candidate built, the complete stack, AI controls, evidence rule, AWS security design, and quality checks. A reviewer could find those facts in the surrounding sections, but had to assemble them from multiple paragraphs and headings.

## Exact changes made

- Made the opening sentence explicitly describe the project as end-to-end.
- Changed the bare live-demo URL into a descriptive link.
- Added a concise `At a glance` table immediately below the demo link, covering the verified implementation, stack, controlled tool calling, authoritative evidence, recommendation guardrail, CloudFront-only signed Lambda-origin access, Terraform, CI, and synthetic-data scope.
- Added the completed Task 023 record to `ROADMAP.md`.

The detailed architecture, deployment, and local-development sections were intentionally retained; the change improves first-pass readability without removing useful technical depth.

## Claims deliberately avoided

- No claim of production-grade hardening, zero-cost operation, uptime, performance, usage, customer adoption, or business impact.
- No claim of authentication, persistent conversations, RAG, agent frameworks, direct model database access, CI/CD deployment, or services not present in the repository.
- No claim that a provider or agent request was exercised during this task.

## Live-demo and endpoint verification

- `GET https://d10nfs9ms4ms1h.cloudfront.net/` returned HTTP 200 (`text/html`).
- `GET https://d10nfs9ms4ms1h.cloudfront.net/api/health` returned HTTP 200 (`application/json`).
- No request was made to `/api/agent/query`.
- No OpenRouter or OpenAI provider/model request was sent.

## Verification

- Confirmed the requested starting state: clean `main` at `efd75a146d2f801746922c9304ea920bfd088ffb`.
- Confirmed the referenced screenshot paths exist and visually reviewed both images.
- Reviewed `.github/workflows/ci.yml`: independent backend and frontend quality jobs run tests, linting, type checks, and compile/build checks.
- Reviewed the agent implementation and tests to validate the configured OpenRouter endpoint and model, allowlisted sequential tools, `parallel_tool_calls=False`, `MAX_TOOL_CALLS=4`, application-owned evidence, and evidence-backed recommendation behavior.
- Ran `git diff --check` and reviewed the final documentation-only diff.

## Confirmed unchanged

- Runtime and backend behavior
- Frontend behavior
- Terraform and AWS resources
- Secrets, container images, ECR lifecycle policy, deployment state, and provider configuration

## Relevant decisions and recommendations outside the repository

- Keep the live demo link near the top of the GitHub repository description or pinned-repository context so a recruiter can open it without first reading the README.
- Use the concise verified claims from the README's `At a glance` section when describing the project on a resume or portfolio; link to the repository and live demo rather than making unsupported outcome or scale claims.
- Keep AWS rollback-material cleanup separate and only perform it after the retention decision recorded in Task 022 is re-validated.

## Recommended next task

No repository change is required for recruiter presentation. If desired, perform the separately authorized Task 022 cleanup review after its intended rollback-retention window.
