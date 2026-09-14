# OpsPilot

OpsPilot is a focused AI Business Operations Agent portfolio project. It is being built to turn structured operational data into evidence-based business decisions.

## Status

The application foundation, synthetic business-data layer, and a controlled OpenAI multi-tool reasoning flow are in place. The backend provides a health endpoint plus deterministic product, sales, inventory, and campaign queries.

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

Copy `.env.example` to `.env` if you need to override the safe development defaults. Supported settings are `APP_ENV`, `DATABASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL`. The default model setting is `gpt-5.6-luna`; provide your own OpenAI API key locally and never commit it.

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

The query services live in `app.services.business_queries` and return structured Python data. They are wrapped only by the constrained Task 004 tool dispatcher, not exposed as direct business-data API endpoints.

## OpenAI business reasoning

`POST /api/agent/query` accepts one business question, for example:

```json
{"question":"Compare FW-100 sales and inventory. Is there a replenishment risk and what should we do?"}
```

The model may select the deterministic `get_product_details`, `query_sales`, `query_inventory`, and `query_campaigns` tools sequentially when a question needs more than one data source. The LLM never accesses SQLAlchemy models or the database directly: a fixed schema and dispatcher validate each selected tool and call the existing query service.

The API returns a structured answer, an evidence-based recommendation when available, and evidence records produced from actual executed tool results. A maximum of four tool calls applies to each question, and repeated identical validated tool requests stop with a controlled result. All business data remains synthetic. The frontend workspace supports asking questions and inspecting answers, recommendations, and evidence.

## Frontend local setup

From `frontend/`, install dependencies and start Vite on <http://localhost:5173>:

```powershell
npm install
npm run dev
```

Start the backend separately on <http://localhost:8000>. Vite proxies `/api` requests to that local backend, so the workspace can query the agent without frontend CORS configuration. Use the supplied example questions or enter your own question to review the answer, recommendation, and traceable synthetic business evidence.

Run frontend checks from `frontend/`:

```powershell
npm test -- --run
npm run lint
npm run build
```

See [ROADMAP.md](ROADMAP.md) for the planned delivery sequence.
