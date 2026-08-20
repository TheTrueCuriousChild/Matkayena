"""Health and readiness endpoints for Server 3."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.services.shared.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {
        "status": "healthy",
        "service": "action_commission_server",
        "version": "1.0.0"
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"degraded: {e}"

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "service": "action_commission_server",
        "database": db_status
    }
