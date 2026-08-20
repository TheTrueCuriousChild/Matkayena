"""Action endpoints for Core Server (delegates lifecycle and commission to Server 3)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.services.shared.auth import get_current_user, UserContext, RoleEnum
from backend.services.shared.config import settings
from backend.services.shared.database import get_db
from backend.services.shared.errors import AuthorizationError, NotFoundError
from backend.services.shared.http_client import ServiceClient
from backend.services.shared.models import Action
from backend.services.shared.repositories.action_repo import ActionRepository

router = APIRouter(prefix="/api/v1/actions", tags=["Actions"])
action_client = ServiceClient("action_commission_server", settings.ACTION_COMMISSION_SERVER_URL)


class CompleteActionRequest(BaseModel):
    outcome_type: str = Field(
        ...,
        description="Outcome of the interaction: CONVERTED, INTERESTED_FOLLOWUP, REJECTED, NOT_REACHABLE",
        examples=["CONVERTED", "INTERESTED_FOLLOWUP"]
    )
    notes: Optional[str] = Field(
        default=None,
        description="Interaction summary or conversion notes",
        examples=["Customer purchased ₹5,00,000 comprehensive term insurance policy."]
    )
    converted_product_id: Optional[str] = Field(
        default=None,
        description="ID of the converted product (e.g. 'prod_ins_1')",
        examples=["prod_ins_1", "prod_mf_1"]
    )
    converted_value: Optional[float] = Field(
        default=None,
        description="Deal size or investment amount converted in INR",
        examples=[500000.0, 1000000.0]
    )
    commission_eligible: bool = Field(
        default=True,
        description="Flag indicating if this deal is eligible for RM commission calculation"
    )


class SnoozeActionRequest(BaseModel):
    snooze_until: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp until which the task is snoozed",
        examples=["2026-08-25T10:00:00Z"]
    )
    reason: str = Field(
        default="Snoozed by RM",
        description="Reason for snoozing the follow-up task",
        examples=["Customer requested callback next week after travel."]
    )


class ReassignActionRequest(BaseModel):
    new_rm_id: str = Field(
        ...,
        description="User ID of the new Relationship Manager to assign",
        examples=["rm_rohan_02"]
    )
    reason: Optional[str] = Field(
        default="Reassigned by manager",
        description="Manager's reason for task reassignment",
        examples=["Reassigned to specialist insurance advisor."]
    )



@router.get(
    "",
    summary="List Actionable RM Tasks",
    description="Retrieves assigned action items for the RM or customer."
)
@router.get(
    "/list-actions",
    summary="List Actionable RM Tasks (Descriptive Alias)",
    description="Retrieves assigned action items for the RM or customer."
)
def list_actions(
    rm_id: Optional[str] = Query(None, description="Relationship Manager ID (e.g. 'rm_priya_01')"),
    customer_id: Optional[str] = Query(None, description="Customer ID to filter tasks (e.g. 'cust_101')"),
    status: Optional[str] = Query(None, description="Task status: PROPOSED, ASSIGNED, IN_PROGRESS, COMPLETED, SNOOZED"),
    limit: int = Query(50, ge=1, le=200, description="Max number of actions to fetch"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Lists actions with server-side authorization checks."""
    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and rm_id and rm_id != user.user_id:
        raise AuthorizationError("Access denied: You cannot view tasks belonging to another RM")

    target_rm_id = rm_id or (user.user_id if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) else None)

    if target_rm_id:
        return ActionRepository.list_by_rm(db, rm_id=target_rm_id, status=status, limit=limit)

    query = db.query(Action)
    if status:
        query = query.filter(Action.status == status)
    if customer_id:
        query = query.filter(Action.customer_id == customer_id)
    return query.order_by(Action.created_at.desc()).limit(limit).all()


@router.get(
    "/{action_id}",
    summary="Get Action Task Details & History",
    description="Fetches action task details, recorded outcome, and full lifecycle transition history."
)
def get_action(
    action_id: str = Path(..., description="Unique Action Task identifier", examples=["act_101"]),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    action = ActionRepository.get_by_id(db, action_id)
    if not action:
        raise NotFoundError("Action", action_id)

    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and action.assigned_rm_id != user.user_id:
        raise AuthorizationError("Access denied: You do not own this action")

    outcome = ActionRepository.get_outcome(db, action_id)
    history = ActionRepository.get_history(db, action_id)
    return {"action": action, "outcome": outcome, "history": history}


@router.post(
    "/{action_id}/complete",
    summary="Complete Action & Compute Deterministic Commission",
    description="Marks action COMPLETED with outcome (e.g. CONVERTED). Calculates deterministic commission with 0% LLM involvement."
)
@router.post(
    "/{action_id}/complete-conversion",
    summary="Complete Action & Compute Commission (Descriptive Alias)",
    description="Marks action COMPLETED with outcome (e.g. CONVERTED). Calculates deterministic commission with 0% LLM involvement."
)
async def complete_action(
    action_id: str = Path(..., description="Unique Action Task identifier to complete", examples=["act_101"]),
    req: CompleteActionRequest = None,
    request: Request = None,
    user: UserContext = Depends(get_current_user)
):
    """Completes an action and calculates deterministic commission via Server 3."""
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)

    return await action_client.post(
        endpoint=f"/api/v1/actions/{action_id}/complete",
        json_data=req.model_dump() if req else {},
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )


@router.post(
    "/{action_id}/snooze",
    summary="Snooze Action Task",
    description="Defers follow-up task to a future time."
)
async def snooze_action(
    action_id: str = Path(..., description="Unique Action Task identifier to snooze", examples=["act_101"]),
    req: SnoozeActionRequest = None,
    request: Request = None,
    user: UserContext = Depends(get_current_user)
):
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)

    return await action_client.post(
        endpoint=f"/api/v1/actions/{action_id}/snooze",
        json_data=req.model_dump() if req else {},
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )


@router.post(
    "/{action_id}/reassign",
    summary="Reassign Action Task",
    description="Reassigns task to a new RM (requires Manager/Admin)."
)
async def reassign_action(
    action_id: str = Path(..., description="Unique Action Task identifier to reassign", examples=["act_101"]),
    req: ReassignActionRequest = None,
    request: Request = None,
    user: UserContext = Depends(get_current_user)
):
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)

    return await action_client.post(
        endpoint=f"/api/v1/actions/{action_id}/reassign",
        json_data=req.model_dump() if req else {},
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )
