"""Opportunity endpoints for Core Server."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.services.shared.auth import get_current_user, UserContext, RoleEnum
from backend.services.shared.config import settings
from backend.services.shared.database import get_db
from backend.services.shared.errors import AuthorizationError, NotFoundError
from backend.services.shared.http_client import ServiceClient
from backend.services.shared.models import Opportunity
from backend.services.shared.repositories.opportunity_repo import OpportunityRepository

router = APIRouter(prefix="/api/v1/opportunities", tags=["Opportunities"])
event_client = ServiceClient("event_intelligence_server", settings.EVENT_INTELLIGENCE_SERVER_URL)


class EvaluateOpportunityRequest(BaseModel):
    customer_id: str = Field(
        ...,
        description="Unique customer ID to evaluate for commercial cross-sell, upsell, and reactivation",
        examples=["cust_101"]
    )


@router.post(
    "/evaluate",
    status_code=status.HTTP_200_OK,
    summary="Evaluate Customer for Opportunities",
    description="Directly invokes Opportunity Agent to detect cross-sell, upsell, and portfolio gaps."
)
@router.post(
    "/evaluate-customer",
    status_code=status.HTTP_200_OK,
    summary="Evaluate Customer for Opportunities (Descriptive Alias)",
    description="Directly invokes Opportunity Agent to detect cross-sell, upsell, and portfolio gaps."
)
async def evaluate_customer_opportunities(
    req: EvaluateOpportunityRequest,
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    """Directly triggers Opportunity Agent evaluation on Server 2."""
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)

    return await event_client.post(
        endpoint="/api/v1/intelligence/evaluate-customer",
        json_data={"customer_id": req.customer_id, "correlation_id": correlation_id},
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )


@router.get(
    "",
    summary="List Detected Commercial Opportunities",
    description="Lists opportunities filtered by RM, customer, or status with deterministic scores."
)
@router.get(
    "/list-opportunities",
    summary="List Detected Commercial Opportunities (Descriptive Alias)",
    description="Lists opportunities filtered by RM, customer, or status with deterministic scores."
)
def list_opportunities(
    rm_id: Optional[str] = Query(None, description="Filter by Relationship Manager ID (e.g. 'rm_priya_01')"),
    customer_id: Optional[str] = Query(None, description="Filter by Customer ID (e.g. 'cust_101')"),
    status: Optional[str] = Query(None, description="Filter by status: DETECTED, ASSIGNED, CONTACTED, CONVERTED"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):

    """Lists commercial opportunities. Enforces RBAC permissions."""
    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and rm_id and rm_id != user.user_id:
        raise AuthorizationError("Access denied: You cannot view opportunities belonging to another RM")

    target_rm_id = rm_id or (user.user_id if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) else None)

    if target_rm_id:
        return OpportunityRepository.list_by_rm(db, rm_id=target_rm_id, status=status, limit=limit)

    query = db.query(Opportunity)
    if status:
        query = query.filter(Opportunity.status == status)
    if customer_id:
        query = query.filter(Opportunity.customer_id == customer_id)
    return query.order_by(Opportunity.score.desc()).limit(limit).all()


@router.get("/{opportunity_id}")
def get_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Fetches full opportunity details, score breakdown, and deterministic explainability."""
    opp = OpportunityRepository.get_by_id(db, opportunity_id)
    if not opp:
        raise NotFoundError("Opportunity", opportunity_id)

    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and opp.rm_id != user.user_id:
        raise AuthorizationError("Access denied: You do not own this opportunity")

    return opp
