from fastapi import FastAPI

from app.api.routes.agent import router as agent_router
from app.api.routes.health import router as health_router

app = FastAPI(title="OpsPilot API")
app.include_router(health_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
