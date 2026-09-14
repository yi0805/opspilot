# OpsPilot

OpsPilot is a focused AI Business Operations Agent portfolio project. It is being built to turn structured operational data into evidence-based business decisions.

## Status

The application foundation and a synthetic business-data layer are in place. The backend provides a health endpoint plus deterministic product, sales, inventory, and campaign queries. AI and agent functionality are not implemented yet.

## Repository structure

```text
backend/    FastAPI application, configuration, SQLAlchemy foundation, and pytest tests
frontend/   React, TypeScript, Vite application and Vitest tests
docs/       Task handoffs
```

## Backend local setup

From `backend/`, create and activate a virtual environment, then install the project with development dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` if you need to override the safe development defaults. Supported settings are `APP_ENV` and `DATABASE_URL`.

Run the API on <http://localhost:8000>:

```powershell
uvicorn app.main:app --reload
```

The health endpoint is `GET /api/health` at <http://localhost:8000/api/health>. It returns `{"status":"ok"}` and does not require PostgreSQL to be running.

Run backend tests from `backend/`:

```powershell
pytest
```

## Synthetic business data

Task 002 adds compact, deterministic demo data for products, aggregated daily sales, current inventory, and marketing campaigns. It is entirely synthetic and does not represent a real company. The data intentionally includes a fast-selling, low-stock product; a low-selling product with excess stock; and both strong and weak campaign ROI.

Seed the configured database from `backend/`:

```powershell
python -m app.db.seed
```

The seed command creates the business tables and inserts the demo data once; later runs leave existing data unchanged. The default configuration targets local PostgreSQL. For a disposable SQLite demo database, set `DATABASE_URL` first:

```powershell
$env:DATABASE_URL = "sqlite:///./opspilot-demo.db"
python -m app.db.seed
```

The query services live in `app.services.business_queries` and return structured Python data for future AI tool wrapping; they are not API endpoints or LLM tools.

## Frontend local setup

From `frontend/`, install dependencies and start Vite on <http://localhost:5173>:

```powershell
npm install
npm run dev
```

Run frontend checks from `frontend/`:

```powershell
npm test -- --run
npm run lint
npm run build
```

See [ROADMAP.md](ROADMAP.md) for the planned delivery sequence.
