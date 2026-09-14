from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return the application's deterministic health status without using the database."""
    return {"status": "ok"}
