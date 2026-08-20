"""Action lifecycle state machine and validation."""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
from backend.services.shared.errors import BadRequestError, NotFoundError
from backend.services.shared.models import Action, ActionHistory
from backend.services.shared.repositories.action_repo import ActionRepository


class ActionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SNOOZED = "SNOOZED"
    REASSIGNED = "REASSIGNED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


VALID_TRANSITIONS: Dict[str, Set[str]] = {
    ActionStatus.PROPOSED.value: {
        ActionStatus.VALIDATED.value, ActionStatus.ASSIGNED.value, ActionStatus.REJECTED.value, ActionStatus.EXPIRED.value
    },
    ActionStatus.VALIDATED.value: {
        ActionStatus.ASSIGNED.value, ActionStatus.IN_PROGRESS.value, ActionStatus.REJECTED.value, ActionStatus.EXPIRED.value
    },
    ActionStatus.ASSIGNED.value: {
        ActionStatus.IN_PROGRESS.value, ActionStatus.SNOOZED.value, ActionStatus.REASSIGNED.value, ActionStatus.REJECTED.value, ActionStatus.EXPIRED.value
    },
    ActionStatus.IN_PROGRESS.value: {
        ActionStatus.COMPLETED.value, ActionStatus.SNOOZED.value, ActionStatus.REASSIGNED.value, ActionStatus.FAILED.value, ActionStatus.REJECTED.value
    },
    ActionStatus.SNOOZED.value: {
        ActionStatus.ASSIGNED.value, ActionStatus.IN_PROGRESS.value, ActionStatus.REASSIGNED.value, ActionStatus.REJECTED.value, ActionStatus.EXPIRED.value
    },
    ActionStatus.REASSIGNED.value: {
        ActionStatus.ASSIGNED.value, ActionStatus.IN_PROGRESS.value, ActionStatus.REJECTED.value
    },
    ActionStatus.COMPLETED.value: set(),  # Terminal state
    ActionStatus.REJECTED.value: set(),   # Terminal state
    ActionStatus.FAILED.value: {ActionStatus.IN_PROGRESS.value, ActionStatus.ASSIGNED.value},  # Can retry
    ActionStatus.EXPIRED.value: set(),    # Terminal state
}


class ActionLifecycleManager:
    @staticmethod
    def validate_transition(current_status: str, target_status: str) -> None:
        """Ensures that the state transition obeys strict state machine rules."""
        if current_status == target_status:
            return

        allowed = VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise BadRequestError(
                f"Invalid action state transition from '{current_status}' to '{target_status}'. "
                f"Allowed transitions: {list(allowed) if allowed else 'None (Terminal state)'}"
            )

    @classmethod
    def transition(
        cls,
        db: Session,
        action_id: str,
        target_status: str,
        changed_by_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Action:
        action = ActionRepository.get_by_id(db, action_id)
        if not action:
            raise NotFoundError("Action", action_id)

        cls.validate_transition(action.status, target_status)
        updated = ActionRepository.update_status(
            db=db,
            action_id=action_id,
            new_status=target_status,
            changed_by_id=changed_by_id,
            reason=reason
        )
        return updated

    @classmethod
    def reassign(
        cls,
        db: Session,
        action_id: str,
        new_rm_id: str,
        changed_by_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Action:
        action = ActionRepository.get_by_id(db, action_id)
        if not action:
            raise NotFoundError("Action", action_id)

        cls.validate_transition(action.status, ActionStatus.REASSIGNED.value)

        # Update RM and status
        action.assigned_rm_id = new_rm_id
        action.status = ActionStatus.ASSIGNED.value
        action.updated_at = datetime.now(timezone.utc)

        history = ActionHistory(
            action_id=action.id,
            previous_status=action.status,
            new_status=ActionStatus.ASSIGNED.value,
            changed_by_id=changed_by_id,
            reason=reason or f"Reassigned to RM {new_rm_id}"
        )
        db.add(history)
        db.commit()
        db.refresh(action)
        return action
