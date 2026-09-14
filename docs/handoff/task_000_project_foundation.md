# Task 000 — Project Foundation

## Task

Task 000 — Project Foundation

## Goal

Establish project documentation, engineering rules, roadmap, and task workflow without implementing application code.

## Git context

- **Branch:** `task/000-project-foundation`
- **Base commit:** `e583beb` (`Initial commit`)
- **Final commit:** the commit containing this handoff document
- **Pull request:** none

## Key changes

- Added root-level `AGENTS.md` with persistent engineering, scope, Git, completion, and handoff rules.
- Added `ROADMAP.md` defining Tasks 001–007 and their intended scope.
- Updated `README.md` to accurately describe the project as early development and link to the roadmap.
- Created the required `docs/handoff/` structure and this Task 000 handoff.

## Verification/tests

- Reviewed the Git diff and status before commit.
- No application code, dependencies, infrastructure, CI, or deployment configuration was added.
- No automated tests apply because this task changes documentation only.

## Known limitations

- The backend, frontend, database, LLM integration, tests, CI, and deployment are intentionally not implemented yet.

## Relevant decisions

- The project will emphasise LLM tool use and structured business workflow automation rather than RAG.
- The next implementation task is constrained to scaffolding the application foundation; it must not implement the LLM agent.

## Recommended next task

Task 001 — Application Scaffold.
