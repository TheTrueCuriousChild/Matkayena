"""Action execution, lifecycle management, and deterministic commission endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.services.action_commission_server.actions.lifecycle_manager import ActionLifecycleManager, ActionStatus
from backend.services.action_commission_server.commission.engine import DeterministicCommissionEngine
from backend.services.shared.auth import get_current_user, require_service_auth, UserContext, RoleEnum
from backend.services.shared.config import settings
from backend.services.shared.database import get_db
from backend.services.shared.errors import AuthorizationError, BadRequestError, NotFoundError
from backend.services.shared.http_client import ServiceClient
from backend.services.shared.models import Action, ActionOutcome
from backend.services.shared.repositories.action_repo import ActionRepository
from backend.services.shared.repositories.customer_repo import CustomerRepository
from backend.services.shared.repositories.opportunity_repo import OpportunityRepository

router = APIRouter(prefix="/api/v1/actions", tags=["Actions & Commissions"])

audit_client = ServiceClient("audit_blockchain_server", settings.AUDIT_BLOCKCHAIN_SERVER_URL)
event_client = ServiceClient("event_intelligence_server", settings.EVENT_INTELLIGENCE_SERVER_URL)


class CreateActionRequest(BaseModel):
    customer_id: str = Field(
        ...,
        description="Target customer identifier",
        examples=["cust_101"]
    )
    assigned_rm_id: str = Field(
        ...,
        description="Relationship Manager user ID responsible for this action",
        examples=["rm_priya_01"]
    )
    title: str = Field(
        ...,
        description="Clear, actionable task headline",
        examples=["Follow-up: Cross-sell Term Life Insurance"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed context, talking points, and customer signals",
        examples=["Customer has ₹25L in Mutual Funds. Present ₹50L term insurance for asset protection."]
    )
    action_type: str = Field(
        default="CALL_CUSTOMER",
        description="Action format: CALL_CUSTOMER, SCHEDULE_MEETING, SEND_PROPOSAL, REVIEW_PORTFOLIO, OFFER_PRODUCT",
        examples=["CALL_CUSTOMER", "OFFER_PRODUCT"]
    )
    priority: str = Field(
        default="MEDIUM",
        description="Task priority level: LOW, MEDIUM, HIGH, CRITICAL",
        examples=["HIGH"]
    )
    opportunity_id: Optional[str] = Field(
        default=None,
        description="Associated opportunity ID detected by Opportunity Agent",
        examples=["opp_101"]
    )
    lead_id: Optional[str] = Field(
        default=None,
        description="Associated lead ID if applicable",
        examples=["lead_501"]
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Task SLA deadline timestamp",
        examples=["2026-08-25T18:00:00Z"]
    )
    source_decision_id: Optional[str] = Field(
        default=None,
        description="ID of the intelligence decision that generated this action"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="End-to-end tracing correlation ID",
        examples=["corr_workflow_1001"]
    )


class StatusTransitionRequest(BaseModel):
    new_status: str = Field(
        ...,
        description="Target lifecycle state: PROPOSED, VALIDATED, ASSIGNED, IN_PROGRESS, COMPLETED, SNOOZED, REASSIGNED, FAILED, EXPIRED, REJECTED",
        examples=["IN_PROGRESS"]
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for status transition",
        examples=["RM contacted customer; follow-up meeting scheduled."]
    )


class SnoozeActionRequest(BaseModel):
    snooze_until: Optional[datetime] = Field(
        default=None,
        description="Timestamp until which the action is deferred",
        examples=["2026-08-28T09:00:00Z"]
    )
    reason: str = Field(
        default="Snoozed by RM",
        description="Reason for snoozing",
        examples=["Customer requested follow-up after salary credit on 1st."]
    )


class ReassignActionRequest(BaseModel):
    new_rm_id: str = Field(
        ...,
        description="New Relationship Manager user ID",
        examples=["rm_rohan_02"]
    )
    reason: Optional[str] = Field(
        default="Reassigned by manager",
        description="Manager justification for reassignment",
        examples=["Reassigned to senior wealth advisor for Ultra-HNI portfolio."]
    )


class CompleteActionRequest(BaseModel):
    outcome_type: str = Field(
        ...,
        description="Conversion outcome: CONVERTED, INTERESTED_FOLLOWUP, REJECTED, NOT_REACHABLE",
        examples=["CONVERTED"]
    )
    notes: Optional[str] = Field(
        default=None,
        description="Interaction summary or conversion notes",
        examples=["Customer accepted term life policy recommendation and completed KYC."]
    )
    converted_product_id: Optional[str] = Field(
        default=None,
        description="Product ID converted (e.g. 'prod_ins_1')",
        examples=["prod_ins_1"]
    )
    converted_value: Optional[float] = Field(
        default=None,
        description="Deal size or investment amount converted in INR",
        examples=[500000.0]
    )
    commission_eligible: bool = Field(
        default=True,
        description="Flag indicating whether this deal qualifies for RM commission calculation"
    )



@router.post("", status_code=status.HTTP_201_CREATED)
async def create_action(
    req: CreateActionRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Creates a new actionable RM task."""
    import uuid
    correlation_id = req.correlation_id or str(uuid.uuid4())

    action = Action(
        customer_id=req.customer_id,
        assigned_rm_id=req.assigned_rm_id,
        title=req.title,
        description=req.description,
        action_type=req.action_type,
        status=ActionStatus.PROPOSED.value,
        priority=req.priority,
        opportunity_id=req.opportunity_id,
        lead_id=req.lead_id,
        due_date=req.due_date,
        source_decision_id=req.source_decision_id,
        correlation_id=correlation_id
    )
    action = ActionRepository.create_action(db, action)

    # Immediately validate and assign if created by system/agent
    action = ActionLifecycleManager.transition(
        db=db,
        action_id=action.id,
        target_status=ActionStatus.ASSIGNED.value,
        changed_by_id=user.user_id,
        reason="Action validated and assigned to RM"
    )

    # If linked to an opportunity, advance opportunity status to ASSIGNED
    if action.opportunity_id:
        OpportunityRepository.update_status(db, action.opportunity_id, "ASSIGNED")

    # Record Audit Entry asynchronously/safely
    try:
        await audit_client.post(
            "/api/v1/audit/record",
            json_data={
                "entity_type": "ACTION",
                "entity_id": action.id,
                "action": "ACTION_CREATED",
                "payload": {
                    "action_id": action.id,
                    "title": action.title,
                    "assigned_rm_id": action.assigned_rm_id,
                    "customer_id": action.customer_id,
                    "status": action.status,
                },
                "actor_id": user.user_id,
                "correlation_id": correlation_id
            },
            correlation_id=correlation_id,
            source_service="action_commission_server"
        )
    except Exception:
        pass  # Audit/Blockchain failure isolation

    return action


@router.get("")
def list_actions(
    rm_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Lists actions. Enforces server-side RBAC so RMs can only see their own tasks."""
    target_rm_id = rm_id or (user.user_id if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) else None)

    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and rm_id and rm_id != user.user_id:
        raise AuthorizationError("Access denied: You cannot view tasks belonging to another RM")

    if target_rm_id:
        return ActionRepository.list_by_rm(db, rm_id=target_rm_id, status=status, limit=limit)
    
    # Manager or Admin listing all
    query = db.query(Action)
    if status:
        query = query.filter(Action.status == status)
    if customer_id:
        query = query.filter(Action.customer_id == customer_id)
    return query.order_by(Action.created_at.desc()).limit(limit).all()


@router.get(
    "/{action_id}",
    summary="Get Action Task Details & History",
    description="Retrieves full details, outcome, and audit history for an action."
)
def get_action_details(
    action_id: str = Path(..., description="Unique Action Task identifier", examples=["act_101"]),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Retrieves full details, outcome, and audit history for an action."""
    action = ActionRepository.get_by_id(db, action_id)
    if not action:
        raise NotFoundError("Action", action_id)

    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and action.assigned_rm_id != user.user_id:
        raise AuthorizationError("Access denied: You do not have permission to view this action")

    outcome = ActionRepository.get_outcome(db, action_id)
    history = ActionRepository.get_history(db, action_id)

    return {
        "action": action,
        "outcome": outcome,
        "history": history
    }


@router.post(
    "/{action_id}/status",
    summary="Transition Action Lifecycle State",
    description="Transitions an action status (e.g. to IN_PROGRESS, REJECTED, etc.)."
)
def transition_status(
    action_id: str = Path(..., description="Unique Action Task identifier", examples=["act_101"]),
    req: StatusTransitionRequest = None,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Transitions an action status (e.g. to IN_PROGRESS)."""
    action = ActionRepository.get_by_id(db, action_id)
    if not action:
        raise NotFoundError("Action", action_id)

    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and action.assigned_rm_id != user.user_id:
        raise AuthorizationError("Access denied: You do not own this action")

    updated = ActionLifecycleManager.transition(
        db=db,
        action_id=action_id,
        target_status=req.new_status,
        changed_by_id=user.user_id,
        reason=req.reason
    )
    return updated


@router.post(
    "/{action_id}/snooze",
    summary="Snooze Action Task",
    description="Snoozes an action with reason and optional reminder time."
)
def snooze_action(
    action_id: str = Path(..., description="Unique Action Task identifier to snooze", examples=["act_101"]),
    req: SnoozeActionRequest = None,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Snoozes an action with reason and optional reminder time."""
    action = ActionRepository.get_by_id(db, action_id)
    if not action:
        raise NotFoundError("Action", action_id)

    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and action.assigned_rm_id != user.user_id:
        raise AuthorizationError("Access denied: You do not own this action")

    if req.snooze_until:
        action.due_date = req.snooze_until

    updated = ActionLifecycleManager.transition(
        db=db,
        action_id=action_id,
        target_status=ActionStatus.SNOOZED.value,
        changed_by_id=user.user_id,
        reason=req.reason
    )
    return updated


@router.post(
    "/{action_id}/reassign",
    summary="Reassign Action Task",
    description="Reassigns an action to another RM. Requires Manager or Admin authorization."
)
def reassign_action(
    action_id: str = Path(..., description="Unique Action Task identifier to reassign", examples=["act_101"]),
    req: ReassignActionRequest = None,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Reassigns an action to another RM. Requires Manager or Admin authorization."""
    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]):
        raise AuthorizationError("Only Managers or Admins can reassign RM actions")

    updated = ActionLifecycleManager.reassign(
        db=db,
        action_id=action_id,
        new_rm_id=req.new_rm_id,
        changed_by_id=user.user_id,
        reason=req.reason
    )
    return updated


@router.post(
    "/{action_id}/complete",
    summary="Complete Action & Run Deterministic Commission Engine",
    description="Completes an action, records outcome, and runs deterministic commission engine on conversion."
)
async def complete_action(
    action_id: str = Path(..., description="Unique Action Task identifier to complete", examples=["act_101"]),
    req: CompleteActionRequest = None,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):

    """Completes an action, records outcome, and runs deterministic commission engine on conversion."""
    action = ActionRepository.get_by_id(db, action_id)
    if not action:
        raise NotFoundError("Action", action_id)

    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and action.assigned_rm_id != user.user_id:
        raise AuthorizationError("Access denied: You do not own this action")

    # Check if already has an outcome (idempotency safety)
    existing_outcome = ActionRepository.get_outcome(db, action_id)
    if existing_outcome:
        raise BadRequestError(f"Action {action_id} already has a recorded outcome ({existing_outcome.outcome_type})")

    # 1. Transition action to COMPLETED
    if action.status == ActionStatus.ASSIGNED.value:
        # Move through IN_PROGRESS first to obey state machine
        ActionLifecycleManager.transition(db, action_id, ActionStatus.IN_PROGRESS.value, user.user_id, "In progress")

    action = ActionLifecycleManager.transition(
        db=db,
        action_id=action_id,
        target_status=ActionStatus.COMPLETED.value,
        changed_by_id=user.user_id,
        reason=f"Action completed with outcome: {req.outcome_type}"
    )

    # 2. Record outcome
    outcome = ActionOutcome(
        action_id=action.id,
        outcome_type=req.outcome_type,
        notes=req.notes,
        converted_product_id=req.converted_product_id,
        converted_value=req.converted_value,
        commission_eligible=(req.outcome_type == "CONVERTED" and req.commission_eligible)
    )
    outcome = ActionRepository.record_outcome(db, outcome)

    # 3. If linked to an Opportunity, update Opportunity status
    if action.opportunity_id:
        new_opp_status = "CONVERTED" if req.outcome_type == "CONVERTED" else "LOST"
        OpportunityRepository.update_status(db, action.opportunity_id, new_opp_status)

    # 4. Deterministic Commission Calculation
    commission_result = None
    if outcome.outcome_type == "CONVERTED" and outcome.commission_eligible and (req.converted_value or 0) > 0:
        # Fetch customer segment & product category
        customer = CustomerRepository.get_by_id(db, action.customer_id)
        product = CustomerRepository.get_product_by_id(db, req.converted_product_id) if req.converted_product_id else None

        commission_result = DeterministicCommissionEngine.calculate(
            converted_value=req.converted_value or 0.0,
            product_category=product.category if product else "DEFAULT",
            customer_segment=customer.segment if customer else "RETAIL",
            rm_id=action.assigned_rm_id,
            is_eligible=True,
            rule_version="1.0"
        )

    # 5. Emit Audit Record to Server 4
    try:
        await audit_client.post(
            "/api/v1/audit/record",
            json_data={
                "entity_type": "ACTION_OUTCOME",
                "entity_id": action.id,
                "action": "ACTION_COMPLETED",
                "payload": {
                    "action_id": action.id,
                    "outcome_type": req.outcome_type,
                    "converted_value": req.converted_value,
                    "converted_product_id": req.converted_product_id,
                    "commission": commission_result.model_dump() if commission_result else None
                },
                "actor_id": user.user_id,
                "correlation_id": action.correlation_id,
                "causation_id": action.source_decision_id
            },
            correlation_id=action.correlation_id,
            source_service="action_commission_server"
        )
    except Exception:
        pass  # Blockchain/Audit Failure Isolation

    # 6. Emit downstream CONVERSION_COMPLETED event to Server 2 if converted
    if outcome.outcome_type == "CONVERTED":
        try:
            await event_client.post(
                "/api/v1/events/ingest",
                json_data={
                    "event_type": "CONVERSION_COMPLETED",
                    "entity_type": "ACTION",
                    "entity_id": action.id,
                    "actor_id": user.user_id,
                    "source": "action_commission_server",
                    "payload": {
                        "action_id": action.id,
                        "customer_id": action.customer_id,
                        "rm_id": action.assigned_rm_id,
                        "converted_value": req.converted_value,
                        "product_id": req.converted_product_id,
                        "commission": commission_result.model_dump() if commission_result else None
                    },
                    "correlation_id": action.correlation_id,
                    "causation_id": action.id
                },
                correlation_id=action.correlation_id,
                source_service="action_commission_server"
            )
        except Exception:
            pass  # Failure isolation

    return {
        "success": True,
        "action_id": action.id,
        "status": action.status,
        "outcome": outcome,
        "commission": commission_result
    }
