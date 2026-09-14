# Task 006 — Production Hardening

## Goal

Make OpsPilot portfolio-ready with repeatable quality gates, focused API and frontend boundary coverage, a small configuration/security review, and accurate architecture documentation.

## Git context

- **Branch:** `task/006-production-hardening`
- **Base commit:** `59500cd077e2d23c660b3fe7eac77a6666351082`
- **Pull request:** none yet; no push, PR, or merge was performed.

## Major changes

- Added independent GitHub Actions backend and frontend jobs for pull requests and pushes to `main`.
- Added development-only Ruff and mypy configuration, including Python 3.12 targets and scoped OpenAI SDK type-boundary suppressions for dynamic request schemas.
- Added the explicit frontend `npm run typecheck` command.
- Added direct `POST /api/agent/query` contract, validation, configuration-error, and provider-error tests.
- Added frontend tests for malformed 2xx JSON shapes, unreadable response bodies, and all three incomplete agent statuses.
- Replaced exception-detail responses for controlled LLM configuration/provider failures with stable, user-safe 503 and 502 messages.
- Expanded `.gitignore` for local databases and static-analysis caches, and refreshed the README with architecture, safeguards, quality checks, limitations, and a real workspace screenshot.

## Verification

All automated checks passed without a live OpenAI call or PostgreSQL service:

```text
backend> python -m pytest
Result: 33 passed (one external Starlette/TestClient deprecation warning).

backend> python -m ruff check app tests
Result: All checks passed.

backend> python -m mypy app
Result: Success: no issues found in 21 source files.

backend> python -m compileall -q app tests
Result: passed (no output).

frontend> npm ci
Result: passed; lockfile installation used.

frontend> npm test -- --run
Result: 1 test file, 18 tests passed.

frontend> npm run lint
Result: passed.

frontend> npm run typecheck
Result: passed.

frontend> npm run build
Result: TypeScript and Vite production build passed.
```

## CI architecture

`ci.yml` has two independent Ubuntu jobs. The backend job uses Python 3.12, installs `.[dev]`, and runs Ruff, mypy, pytest, and compileall. The frontend job uses Node 22, installs with `npm ci`, and runs tests, linting, type checking, and the production build. Neither job defines a secret, calls OpenAI, or starts PostgreSQL.

## Configuration and security review

`.env` files remain ignored while `backend/.env.example` contains an empty API-key value only. `OPENAI_API_KEY` remains environment-driven; no tracked database files or API secrets were found, and the frontend and CI contain no secret values. Local `*.db`, `*.sqlite`, `*.sqlite3`, `.mypy_cache/`, and `.ruff_cache/` artifacts are now ignored.

## Screenshot status

Created and visually verified `docs/screenshots/opspilot-workspace.png`: a valid, non-empty 1440×1100 PNG captured from the actual local Vite frontend initial workspace.

## Docker decision

Docker was intentionally deferred. The current application has no concrete container requirement, and deployment architecture belongs to Task 007 rather than speculative Task 006 infrastructure.

## Known limitations

- The data is synthetic and live agent questions require a local OpenAI API key.
- The application has no authentication, user accounts, conversation history, streaming, or deployment.
- The OpenAI SDK's dynamic tool and final-output schema request types use narrowly scoped mypy suppressions at that third-party boundary.

## Recommended next task

Task 007 — AWS and Terraform.
