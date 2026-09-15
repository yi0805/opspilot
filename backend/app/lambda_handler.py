"""Lambda cold-start entrypoint for the OpsPilot FastAPI application."""

from app.core.runtime_secrets import ensure_openai_api_key

ensure_openai_api_key()

from app.db.seed import main as seed_demo_database  # noqa: E402

seed_demo_database()

from mangum import Mangum  # noqa: E402

from app.main import app  # noqa: E402

handler = Mangum(app)
