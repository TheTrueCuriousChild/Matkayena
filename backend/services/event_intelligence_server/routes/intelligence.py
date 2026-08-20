"""Intelligence and direct Agent evaluation endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.services.event_intelligence_server.agents.manager_agent import ManagerAgent, ManagerAlert
from backend.services.event_intelligence_server.agents.opportunity_agent import OpportunityAgent
from backend.services.event_intelligence_server.agents.performance_agent import PerformanceAgent
from backend.services.shared.auth import get_current_user, require_roles, require_service_auth, UserContext, RoleEnum
from backend.services.shared.database import get_db
from backend.services.shared.errors import NotFoundError
from backend.services.shared.repositories.opportunity_repo import OpportunityRepository
from backend.services.shared.repositories.performance_repo import PerformanceRepository

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence & Agents"])


class EvaluateCustomerRequest(BaseModel):
    customer_id: str = Field(
        ...,
        description="Customer ID to evaluate for portfolio cross-sell and reactivation",
        examples=["cust_101"]
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Workflow correlation ID",
        examples=["corr_eval_cust101_01"]
    )


class EvaluatePerformanceRequest(BaseModel):
    rm_id: str = Field(
        ...,
        description="Relationship Manager ID to evaluate",
        examples=["rm_priya_01"]
    )
    period: str = Field(
        default="2026-Q1",
        description="Fiscal evaluation period",
        examples=["2026-Q1", "2026-M03"]
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Workflow correlation ID"
    )


@router.post(
    "/evaluate-customer",
    summary="Agent #1: Evaluate Customer Opportunity",
    description="Invokes Opportunity Agent to inspect customer portfolio and detect cross-sell/reactivation."
)
@router.post(
    "/evaluate-customer-opportunity",
    summary="Agent #1: Evaluate Customer Opportunity (Descriptive Alias)",
    description="Invokes Opportunity Agent to inspect customer portfolio and detect cross-sell/reactivation."
)
async def evaluate_customer(
    req: EvaluateCustomerRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Directly triggers Opportunity Agent evaluation for a specific customer."""
    opps = await OpportunityAgent.evaluate_customer(
        db=db,
        customer_id=req.customer_id,
        correlation_id=req.correlation_id
    )
    return {
        "success": True,
        "customer_id": req.customer_id,
        "opportunities_count": len(opps),
        "opportunities": opps
    }


@router.post(
    "/evaluate-performance",
    summary="Agent #2: Evaluate RM Performance",
    description="Invokes Performance Agent to diagnose pacing, conversion, SLA breaches, and drivers."
)
@router.post(
    "/evaluate-rm-performance",
    summary="Agent #2: Evaluate RM Performance (Descriptive Alias)",
    description="Invokes Performance Agent to diagnose pacing, conversion, SLA breaches, and drivers."
)
async def evaluate_performance(
    req: EvaluatePerformanceRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Triggers Performance Agent to evaluate an RM's metrics and pacing."""
    snapshot = await PerformanceAgent.evaluate_rm(
        db=db,
        rm_id=req.rm_id,
        period=req.period,
        correlation_id=req.correlation_id
    )
    return {
        "success": True,
        "rm_id": req.rm_id,
        "period": req.period,
        "snapshot": snapshot
    }


@router.get(
    "/manager/alerts",
    response_model=List[ManagerAlert],
    summary="Agent #3: Generate Manager Intelligence & Alerts",
    description="Invokes Manager Agent to synthesize high-priority risk alerts, shortfalls, and escalations."
)
@router.get(
    "/manager-intelligence/list-alerts",
    response_model=List[ManagerAlert],
    summary="Agent #3: Manager Intelligence (Descriptive Alias)",
    description="Invokes Manager Agent to synthesize high-priority risk alerts, shortfalls, and escalations."
)
async def get_manager_alerts(
    manager_id: Optional[str] = Query(None, description="Optional manager user ID filter"),
    period: str = Query("2026-Q1", description="Fiscal period to evaluate"),
    correlation_id: Optional[str] = Query(None, description="Workflow correlation ID"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Synthesizes managerial intelligence, risk alerts, escalations, and achievements."""
    target_manager_id = manager_id or (user.user_id if user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) else None)
    alerts = await ManagerAgent.evaluate_manager_intelligence(
        db=db,
        manager_id=target_manager_id,
        period=period
    )
    return alerts


@router.get(
    "/opportunities/{opportunity_id}",
    summary="Get Opportunity Explainability Details",
    description="Fetches opportunity details with full deterministic explainability (what, why, score components, rules)."
)
def get_opportunity_details(
    opportunity_id: str = Path(..., description="Unique Opportunity ID to inspect", examples=["opp_101"]),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Fetches opportunity details with full deterministic explainability."""
    opp = OpportunityRepository.get_by_id(db, opportunity_id)
    if not opp:
        raise NotFoundError("Opportunity", opportunity_id)
    return opp


