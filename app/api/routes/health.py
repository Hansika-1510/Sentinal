from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db
from app.core.config import settings

router = APIRouter(tags=["Health & Status"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Liveness probe."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "llm_provider": settings.LLM_PROVIDER
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe checking database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        return {"status": "unready", "database": f"error: {str(e)}"}

    return {
        "status": "ready",
        "database": db_status,
        "redis": "connected" if settings.REDIS_URL else "in-memory-fallback"
    }
