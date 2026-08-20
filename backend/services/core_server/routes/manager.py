"""Manager intelligence and alerts endpoint for Core Server."""

from typing import Optional
from fastapi import APIRouter, Depends, Request, status
from backend.services.shared.auth import get_current_user, require_roles, UserContext, RoleEnum
from backend.services.shared.config import settings
from backend.services.shared.http_client import ServiceClient

router = APIRouter(prefix="/api/v1/manager", tags=["Manager Intelligence"])
event_client = ServiceClient("event_intelligence_server", settings.EVENT_INTELLIGENCE_SERVER_URL)


@router.get("/alerts")
async def get_manager_alerts(
    period: str = "2026-Q1",
    request: Request = None,
    user: UserContext = Depends(require_roles([RoleEnum.MANAGER.value, RoleEnum.TEAM_LEAD.value, RoleEnum.ADMIN.value]))
):
    """Retrieves prioritized risk alerts, escalations, and coaching recommendations for managers."""
    correlation_id = getattr(request.state, "correlation_id", None) if request else None
    request_id = getattr(request.state, "request_id", None) if request else None

    return await event_client.get(
        endpoint="/api/v1/intelligence/manager/alerts",
        params={"manager_id": user.user_id, "period": period},
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )
