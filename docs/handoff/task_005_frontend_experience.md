# Task 005 — Frontend Experience

## Goal

Build a polished, responsive workspace for asking OpsPilot business questions and reviewing answers, recommendations, and traceable synthetic business evidence.

## Git context

- **Branch:** `task/005-frontend-experience`
- **Base commit:** `47e1aab8ce676df71cdc429b45828c8b7560a82a`
- **Pull request:** [#6 — Task 005: build frontend experience](https://github.com/yi0805/opspilot/pull/6)

## Architecture and decisions

`App` owns question, loading, result, and error state. The typed `api/agent.ts` client uses native fetch against relative `/api/agent/query`, validates the response boundary, and returns safe network/server errors. Vite proxies `/api` to `http://localhost:8000` locally.

Components split the question form, example prompts, result panel, and evidence list. Evidence uses JSON-compatible public contract types: scalar-record arrays render semantic, horizontally scrollable tables; scalar objects render definition rows; empty evidence or record data shows a clear message; nested shapes have a restrained native details fallback.

The light neutral, navy, and restrained-blue visual system is defined with CSS variables. Result cards use two columns on desktop and stack on narrow screens. Focus-visible states, semantic headings, labels, real buttons, status/error live announcements, readable controlled-status labels, and reduced-motion support are included.

Completed results may show recommendations. `tool_error`, `tool_limit_reached`, and `duplicate_tool_call` results are visibly incomplete, retain collected evidence, and do not show a recommendation. Loading disables form controls; the form naturally retries after errors.

## Key changes

- Replaced the static React scaffold with the single-page analysis workspace.
- Added typed API integration and Vite proxy configuration.
- Added result, recommendation, loading/error/status, and generic evidence rendering UX.
- Added behavioral frontend coverage and updated README/roadmap.

## Verification

```text
frontend> npm test -- --run
Result: 1 test file, 14 tests passed.

frontend> npm run lint
Result: passed.

frontend> npm run build
Result: TypeScript and Vite production build passed.

backend> .\.venv\Scripts\python.exe -m pytest
Result: 31 passed; one existing Starlette/TestClient deprecation warning.

backend> .\.venv\Scripts\python.exe -m compileall -q app tests
Result: passed (no output).
```

## Known limitations

- Live answers require a separately running backend with an OpenAI API key; the frontend behavior is covered with mocked API results.
- Streaming, history, authentication, deployment, and Task 006 production hardening are out of scope.

## Recommended next task

Task 006 — Production Hardening.
