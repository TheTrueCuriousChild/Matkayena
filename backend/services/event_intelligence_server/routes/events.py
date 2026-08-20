"""Event ingestion, idempotency deduplication, and agent routing endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from backend.services.event_intelligence_server.agents.opportunity_agent import OpportunityAgent
from backend.services.event_intelligence_server.agents.performance_agent import PerformanceAgent
from backend.services.shared.auth import get_current_user, require_service_auth, UserContext
from backend.services.shared.config import settings
from backend.services.shared.database import get_db
from backend.services.shared.errors import IdempotencyConflictError
from backend.services.shared.events import EventEnvelope, EventProcessingResult, EventSubmissionRequest
from backend.services.shared.http_client import ServiceClient
from backend.services.shared.logging import setup_logger
from backend.services.shared.models import BusinessEvent, EventProcessingAttempt
from backend.services.shared.repositories.event_repo import EventRepository

logger = setup_logger("event_router")
audit_client = ServiceClient("audit_blockchain_server", settings.AUDIT_BLOCKCHAIN_SERVER_URL)

router = APIRouter(prefix="/api/v1/events", tags=["Events & Ingestion"])


@router.post("/ingest", response_model=EventProcessingResult, status_code=status.HTTP_200_OK)
async def ingest_event(
    req: EventSubmissionRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Primary event ingestion gateway.

    Enforces idempotency, routes to Opportunity/Performance agents, and records tamper-evident audit.
    """
    correlation_id = req.correlation_id or str(uuid.uuid4())
    event_id = str(uuid.uuid4())

    # 1. Idempotency Check
    if req.idempotency_key:
        existing = EventRepository.get_by_idempotency_key(db, req.idempotency_key)
        if existing:
            logger.info(f"Duplicate event detected for idempotency_key '{req.idempotency_key}'. Returning existing event.")
            return EventProcessingResult(
                success=True,
                event_id=existing.id,
                correlation_id=existing.correlation_id,
                decisions_made=0,
                actions_created=0,
                message="Duplicate event ignored due to idempotency key match",
                details={"status": "IDEMPOTENT_SUPPRESSION", "original_event_id": existing.id}
            )

    # 2. Persist Business Event
    now = datetime.now(timezone.utc)
    business_event = BusinessEvent(
        id=event_id,
        event_type=req.event_type.value,
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        actor_id=req.actor_id or user.user_id,
        source=req.source or "api",
        payload=req.payload,
        schema_version="1.0",
        correlation_id=correlation_id,
        causation_id=req.causation_id,
        idempotency_key=req.idempotency_key,
        occurred_at=now,
        received_at=now
    )
    business_event = EventRepository.record_event(db, business_event)

    # 3. Create Event Envelope
    envelope = EventEnvelope(
        event_id=business_event.id,
        event_type=req.event_type,
        entity_type=business_event.entity_type,
        entity_id=business_event.entity_id,
        actor_id=business_event.actor_id,
        source=business_event.source,
        payload=business_event.payload,
        correlation_id=correlation_id,
        causation_id=req.causation_id,
        idempotency_key=req.idempotency_key,
        occurred_at=business_event.occurred_at,
        received_at=business_event.received_at
    )

    decisions_count = 0
    actions_count = 0

    # 4. Route to Opportunity Agent
    try:
        opps = await OpportunityAgent.evaluate_event(db, envelope)
        if opps:
            decisions_count += len(opps)
            actions_count += len(opps)
    except Exception as e:
        logger.error(f"Error in OpportunityAgent routing: {e}")

    # 5. Route to Performance Agent if applicable
    try:
        if req.event_type.value in ["CONVERSION_COMPLETED", "ACTION_COMPLETED", "ACTION_SNOOZED"]:
            perf_snapshot = await PerformanceAgent.evaluate_event(db, envelope)
            if perf_snapshot:
                decisions_count += 1
    except Exception as e:
        logger.error(f"Error in PerformanceAgent routing: {e}")

    # 6. Record Processing Attempt
    attempt = EventProcessingAttempt(
        event_id=business_event.id,
        processor_name="event_intelligence_server",
        status="SUCCESS",
        attempt_number=1,
        processed_at=datetime.now(timezone.utc)
    )
    EventRepository.record_attempt(db, attempt)

    # 7. Record Audit proof to Server 4
    try:
        await audit_client.post(
            "/api/v1/audit/record",
            json_data={
                "entity_type": "BUSINESS_EVENT",
                "entity_id": business_event.id,
                "action": f"EVENT_PROCESSED_{business_event.event_type}",
                "payload": {
                    "event_type": business_event.event_type,
                    "entity_type": business_event.entity_type,
                    "entity_id": business_event.entity_id,
                    "decisions_made": decisions_count
                },
                "actor_id": user.user_id,
                "correlation_id": correlation_id,
                "causation_id": req.causation_id
            },
            correlation_id=correlation_id,
            source_service="event_intelligence_server"
        )
    except Exception:
        pass  # Blockchain/Audit failure isolation

    return EventProcessingResult(
        success=True,
        event_id=business_event.id,
        correlation_id=correlation_id,
        decisions_made=decisions_count,
        actions_created=actions_count,
        message="Event processed and routed to intelligence agents successfully",
        details={"event_type": business_event.event_type, "decisions_count": decisions_count}
    )
