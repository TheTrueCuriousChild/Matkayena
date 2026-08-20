"""Standard Event contracts, schemas, and event types for PS-02 closed loop."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field


class EventTypeEnum(str, Enum):
    PAYIN_RECEIVED = "PAYIN_RECEIVED"
    PAYOUT_REQUESTED = "PAYOUT_REQUESTED"
    LEAD_CREATED = "LEAD_CREATED"
    LEAD_UPDATED = "LEAD_UPDATED"
    CUSTOMER_ACTIVITY = "CUSTOMER_ACTIVITY"
    DIGITAL_ACTIVITY = "DIGITAL_ACTIVITY"
    OPPORTUNITY_CREATED = "OPPORTUNITY_CREATED"
    ACTION_CREATED = "ACTION_CREATED"
    ACTION_COMPLETED = "ACTION_COMPLETED"
    ACTION_SNOOZED = "ACTION_SNOOZED"
    ACTION_REASSIGNED = "ACTION_REASSIGNED"
    CONVERSION_COMPLETED = "CONVERSION_COMPLETED"
    COMMISSION_GENERATED = "COMMISSION_GENERATED"
    TARGET_ACHIEVED = "TARGET_ACHIEVED"
    PERFORMANCE_RISK_DETECTED = "PERFORMANCE_RISK_DETECTED"
    MANAGER_ALERT_CREATED = "MANAGER_ALERT_CREATED"


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventTypeEnum
    entity_type: str  # CUSTOMER, LEAD, TRANSACTION, RM, ACTION, OPPORTUNITY
    entity_id: str
    actor_id: Optional[str] = None
    source: str = "system"
    payload: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    causation_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventSubmissionRequest(BaseModel):
    event_type: EventTypeEnum
    entity_type: str
    entity_id: str
    actor_id: Optional[str] = None
    source: Optional[str] = "api"
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class EventProcessingResult(BaseModel):
    success: bool
    event_id: str
    correlation_id: str
    decisions_made: int = 0
    actions_created: int = 0
    message: str = "Event processed successfully"
    details: Optional[Dict[str, Any]] = None
