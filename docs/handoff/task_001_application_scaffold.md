# Task

Task 001 — Application Scaffold

## Goal

Create the minimal, locally runnable OpsPilot application foundation without business-data or AI functionality.

## Git context

- **Branch:** `task/001-application-scaffold`
- **Base commit:** `b11e9c2af1b05a83780b5a46b91e0905994bd85a`
- **Final commit:** the commit containing this handoff document (reported after commit)
- **Pull request:** none; not opened or pushed

## Key changes

- Added a FastAPI backend with deterministic `GET /api/health` response `{ "status": "ok" }`.
- Added environment-based `APP_ENV` and `DATABASE_URL` settings, with documented safe development defaults.
- Added SQLAlchemy declarative base, PostgreSQL engine, and session factory without models, tables, migrations, or connection-on-import behaviour.
- Added a React, TypeScript, and Vite MVP shell with local CSS.
- Added a backend health test and frontend render test.
- Added local-development documentation and a focused root `.gitignore`.

## Backend architecture

- `app/main.py` creates the FastAPI application and mounts API routes under `/api`.
- `app/api/routes/health.py` owns the health route, which does not use the database layer.
- `app/core/config.py` provides cached Pydantic settings from environment variables or `.env`.
- `app/db/base.py` defines the declarative base; `app/db/session.py` creates the SQLAlchemy engine and session factory only.

## Frontend architecture

- `src/App.tsx` renders the minimal OpsPilot MVP status shell.
- Local CSS in `src/App.css` and `src/index.css` provides the styling.
- Vitest with React Testing Library tests that the product name, role, and MVP status render.

## Dependency decisions

- Backend runtime: FastAPI, Uvicorn, SQLAlchemy, Psycopg, and Pydantic Settings.
- Backend development: pytest and HTTPX for FastAPI's TestClient.
- Frontend: React, TypeScript, Vite, Vitest, JSDOM, and React Testing Library.
- No AI SDKs, agent frameworks, database migrations, UI libraries, or infrastructure dependencies were added.

## Verification

The following commands were run successfully:

```text
backend> .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Result: dependencies installed successfully; backend test environment available.

backend> .\.venv\Scripts\python.exe -m pytest
Result: 1 passed.

backend> .\.venv\Scripts\python.exe -c "from app.db.session import engine; from app.main import app; print(app.title); print(engine.url)"
Result: application and SQLAlchemy engine imported successfully without a database connection.

backend> .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
Result: local server started; GET http://127.0.0.1:8000/api/health returned HTTP 200 and {"status":"ok"}.

frontend> npm test -- --run
Result: 1 test file and 1 test passed.

frontend> npm run lint
Result: passed.

frontend> npm run build
Result: TypeScript check and Vite production build passed.
```

## Known limitations

The following are intentionally not implemented: business schema/data, LLM integration, agent logic, tool calling, or deployment.

## Relevant decisions

- The health route does not import or depend on the database session, keeping health checks usable without PostgreSQL.
- The database engine is constructed from configuration but no connection, schema operation, or table creation occurs at import time.
- The frontend remains a static MVP shell until the product experience task.

## Recommended next task

Task 002 — Business Data Layer
