"""Intelligence and direct Agent evaluation endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
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
    customer_id: str
    correlation_id: Optional[str] = None


class EvaluatePerformanceRequest(BaseModel):
    rm_id: str
    period: str = "2026-Q1"
    correlation_id: Optional[str] = None


@router.post("/evaluate-customer")
async def evaluate_customer_direct(
    req: EvaluateCustomerRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Direct Opportunity Agent evaluation on demand for a customer."""
    opps = await OpportunityAgent.evaluate_customer(
        db=db,
        customer_id=req.customer_id,
        correlation_id=req.correlation_id
    )
    return {
        "success": True,
        "customer_id": req.customer_id,
        "opportunities_detected": len(opps),
        "opportunities": opps
    }


@router.post("/evaluate-performance")
async def evaluate_performance_direct(
    req: EvaluatePerformanceRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Direct Performance Agent evaluation on demand for an RM."""
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


@router.get("/manager/alerts", response_model=List[ManagerAlert])
async def get_manager_alerts(
    manager_id: Optional[str] = None,
    period: str = "2026-Q1",
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


@router.get("/opportunities/{opportunity_id}")
def get_opportunity_details(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Fetches opportunity details with full deterministic explainability."""
    opp = OpportunityRepository.get_by_id(db, opportunity_id)
    if not opp:
        raise NotFoundError("Opportunity", opportunity_id)
    return opp
