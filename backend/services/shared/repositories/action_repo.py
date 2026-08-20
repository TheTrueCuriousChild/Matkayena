"""Repository for Actions, Action History, and Action Outcomes."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import Action, ActionHistory, ActionOutcome


class ActionRepository:
    @staticmethod
    def get_by_id(db: Session, action_id: str) -> Optional[Action]:
        return db.query(Action).filter(Action.id == action_id).first()

    @staticmethod
    def list_by_rm(db: Session, rm_id: str, status: Optional[str] = None, limit: int = 100) -> List[Action]:
        query = db.query(Action).filter(Action.assigned_rm_id == rm_id)
        if status:
            query = query.filter(Action.status == status)
        return query.order_by(Action.created_at.desc()).limit(limit).all()

    @staticmethod
    def create_action(db: Session, action: Action) -> Action:
        db.add(action)
        db.commit()
        db.refresh(action)

        # Log initial history
        history = ActionHistory(
            action_id=action.id,
            previous_status="NONE",
            new_status=action.status,
            changed_by_id=action.assigned_rm_id,
            reason="Action created"
        )
        db.add(history)
        db.commit()

        return action

    @staticmethod
    def update_status(
        db: Session,
        action_id: str,
        new_status: str,
        changed_by_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Optional[Action]:
        action = db.query(Action).filter(Action.id == action_id).first()
        if not action:
            return None

        prev_status = action.status
        action.status = new_status
        action.updated_at = datetime.now(timezone.utc)

        # Record history
        history = ActionHistory(
            action_id=action.id,
            previous_status=prev_status,
            new_status=new_status,
            changed_by_id=changed_by_id,
            reason=reason or f"Status changed from {prev_status} to {new_status}"
        )
        db.add(history)
        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def record_outcome(db: Session, outcome: ActionOutcome) -> ActionOutcome:
        db.add(outcome)
        db.commit()
        db.refresh(outcome)
        return outcome

    @staticmethod
    def get_outcome(db: Session, action_id: str) -> Optional[ActionOutcome]:
        return db.query(ActionOutcome).filter(ActionOutcome.action_id == action_id).first()

    @staticmethod
    def get_history(db: Session, action_id: str) -> List[ActionHistory]:
        return db.query(ActionHistory).filter(ActionHistory.action_id == action_id).order_by(ActionHistory.created_at.asc()).all()
