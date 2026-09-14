# Project Goal

OpsPilot is a focused AI Business Operations Agent and a portfolio-quality proof of concept. It will demonstrate practical business-data analysis and workflow automation through a deliberately small, understandable application.

# Engineering Principles

- Keep the implementation small, explicit, and understandable.
- Prefer simple solutions over unnecessary abstractions.
- Do not overengineer.
- Work on one roadmap task at a time.
- Do not implement features outside the active task.
- Maintain clear boundaries between API routes, services, data access, agent/tool logic, and frontend concerns.
- Add meaningful tests for important behaviour.
- Run applicable tests, linting, type checking, and builds before declaring a task complete.
- Never claim functionality that has not actually been verified.
- Do not hide failures or skip broken checks.
- Keep documentation consistent with the actual implementation.

# Scope Restrictions

Do not add the following unless a later task explicitly requests them:

- authentication
- user accounts
- multi-agent frameworks
- MCP
- Databricks
- dbt
- Kubernetes
- complex design systems
- unnecessary cloud services
- unnecessary dependencies
- speculative features

Do not add RAG unless explicitly requested. WhereRU already demonstrates RAG; OpsPilot should primarily demonstrate agent/tool use and business workflow automation.

# Git Workflow

- Never work directly on `main` for implementation tasks.
- Each task must use a dedicated branch named `task/XXX-description`.
- Keep changes scoped to the current task.
- Make clear commits.
- Do not merge pull requests automatically.
- Do not rewrite unrelated history.
- Report the branch, base commit, final commit, and changed files at task completion.
- Open a pull request only when explicitly requested by the task or user.

# Task Completion

Before reporting a task complete:

- run relevant tests and checks
- fix failures caused by the task
- review the Git diff
- confirm no unrelated files were changed
- update `ROADMAP.md` accurately
- create or update the corresponding handoff document under `docs/handoff/`

# Handoff Documents

Use the path `docs/handoff/task_XXX_<short_name>.md`.

Each handoff must record:

- task
- goal
- branch
- base commit
- final commit
- pull request, if applicable
- key changes
- verification/tests
- known limitations
- relevant decisions
- recommended next task

Handoffs must describe reality, not planned or unverified behaviour.
