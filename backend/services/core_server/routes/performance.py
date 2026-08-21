"""Performance endpoints for Core Server."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, Request, status
from sqlalchemy.orm import Session
from backend.services.shared.auth import get_current_user, UserContext, RoleEnum
from backend.services.shared.config import settings
from backend.services.shared.database import get_db
from backend.services.shared.errors import AuthorizationError
from backend.services.shared.http_client import ServiceClient
from backend.services.shared.repositories.performance_repo import PerformanceRepository

router = APIRouter(prefix="/api/v1/performance", tags=["Performance & Analytics"])
event_client = ServiceClient("event_intelligence_server", settings.EVENT_INTELLIGENCE_SERVER_URL)


# NOTE: Static paths MUST be registered before dynamic /{rm_id} to avoid shadowing.
@router.get(
    "/achievements/all",
    summary="List RM Achievements & Milestone Awards",
    description="Lists all performance achievements (e.g. EARLY_TARGET_ACHIEVEMENT, MAJOR_WIN)."
)
@router.get(
    "/achievements/list",
    summary="List RM Achievements (Descriptive Alias)",
    description="Lists all performance achievements (e.g. EARLY_TARGET_ACHIEVEMENT, MAJOR_WIN)."
)
def list_achievements(
    rm_id: Optional[str] = Query(None, description="Optional RM ID filter"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):

    target_rm_id = rm_id or (user.user_id if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) else None)
    return PerformanceRepository.list_achievements(db, rm_id=target_rm_id)


@router.get(
    "/{rm_id}",
    summary="Evaluate RM Performance Intelligence",
    description="Computes target achievement, run-rate pacing, conversion rates, follow-up SLA scores, and status diagnostics."
)
@router.get(
    "/evaluate-rm/{rm_id}",
    summary="Evaluate RM Performance Intelligence (Descriptive Alias)",
    description="Computes target achievement, run-rate pacing, conversion rates, follow-up SLA scores, and status diagnostics."
)
async def get_rm_performance(
    rm_id: str = Path(..., description="Relationship Manager user ID (e.g. 'rm_priya_01')", examples=["rm_priya_01"]),
    period: str = Query("2026-Q3", description="Fiscal evaluation period (e.g. '2026-Q3', '2026-M08')"),
    request: Request = None,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):

    """Retrieves or evaluates comprehensive performance intelligence for an RM."""
    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and rm_id != user.user_id:
        raise AuthorizationError("Access denied: You cannot view performance diagnostics for another RM")

    # Delegate to Server 2 Performance Agent
    correlation_id = getattr(request.state, "correlation_id", None) if request else None
    request_id = getattr(request.state, "request_id", None) if request else None

    return await event_client.post(
        endpoint="/api/v1/intelligence/evaluate-performance",
        json_data={"rm_id": rm_id, "period": period, "correlation_id": correlation_id},
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )
