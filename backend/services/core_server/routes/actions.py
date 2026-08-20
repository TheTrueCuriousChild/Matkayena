"""Action endpoints for Core Server (delegates lifecycle and commission to Server 3)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel
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
    outcome_type: str  # CONVERTED, INTERESTED_FOLLOWUP, REJECTED, NOT_REACHABLE
    notes: Optional[str] = None
    converted_product_id: Optional[str] = None
    converted_value: Optional[float] = None
    commission_eligible: bool = True


class SnoozeActionRequest(BaseModel):
    snooze_until: Optional[str] = None
    reason: str = "Snoozed by RM"


class ReassignActionRequest(BaseModel):
    new_rm_id: str
    reason: Optional[str] = "Reassigned by manager"


@router.get("")
def list_actions(
    rm_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Lists RM actions with server-side authorization checks."""
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


@router.get("/{action_id}")
def get_action(
    action_id: str,
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


@router.post("/{action_id}/complete")
async def complete_action(
    action_id: str,
    req: CompleteActionRequest,
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    """Completes an action and calculates deterministic commission via Server 3."""
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)

    return await action_client.post(
        endpoint=f"/api/v1/actions/{action_id}/complete",
        json_data=req.model_dump(mode="json"),
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )


@router.post("/{action_id}/snooze")
async def snooze_action(
    action_id: str,
    req: SnoozeActionRequest,
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)

    return await action_client.post(
        endpoint=f"/api/v1/actions/{action_id}/snooze",
        json_data=req.model_dump(mode="json"),
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )


@router.post("/{action_id}/reassign")
async def reassign_action(
    action_id: str,
    req: ReassignActionRequest,
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    correlation_id = getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)

    return await action_client.post(
        endpoint=f"/api/v1/actions/{action_id}/reassign",
        json_data=req.model_dump(mode="json"),
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )
