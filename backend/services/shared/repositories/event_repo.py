"""Repository for Event Ingestion and Processing History."""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import BusinessEvent, EventProcessingAttempt, EventType


class EventRepository:
    @staticmethod
    def get_by_id(db: Session, event_id: str) -> Optional[BusinessEvent]:
        return db.query(BusinessEvent).filter(BusinessEvent.id == event_id).first()

    @staticmethod
    def get_by_idempotency_key(db: Session, idempotency_key: str) -> Optional[BusinessEvent]:
        if not idempotency_key:
            return None
        return db.query(BusinessEvent).filter(BusinessEvent.idempotency_key == idempotency_key).first()

    @staticmethod
    def record_event(db: Session, event: BusinessEvent) -> BusinessEvent:
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def record_attempt(db: Session, attempt: EventProcessingAttempt) -> EventProcessingAttempt:
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def list_by_correlation_id(db: Session, correlation_id: str) -> List[BusinessEvent]:
        return db.query(BusinessEvent).filter(
            BusinessEvent.correlation_id == correlation_id
        ).order_by(BusinessEvent.received_at.asc()).all()

    @staticmethod
    def list_by_entity(db: Session, entity_type: str, entity_id: str, limit: int = 50) -> List[BusinessEvent]:
        query = db.query(BusinessEvent)
        if entity_type.upper() == "CUSTOMER":
            query = query.filter(BusinessEvent.customer_id == entity_id)
        elif entity_type.upper() == "LEAD":
            query = query.filter(BusinessEvent.lead_id == entity_id)
        return query.order_by(BusinessEvent.received_at.desc()).limit(limit).all()

