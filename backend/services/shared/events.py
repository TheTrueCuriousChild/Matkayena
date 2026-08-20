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
    event_type: EventTypeEnum = Field(
        ...,
        description="Type of event triggering the intelligence loop",
        examples=["PAYIN_RECEIVED", "LEAD_CREATED", "CUSTOMER_ACTIVITY"]
    )
    entity_type: str = Field(
        ...,
        description="Target entity type",
        examples=["CUSTOMER", "LEAD", "TRANSACTION", "RM"]
    )
    entity_id: str = Field(
        ...,
        description="Unique identifier of the customer, lead, or transaction",
        examples=["cust_101", "lead_501", "tx_901"]
    )
    actor_id: Optional[str] = Field(
        default=None,
        description="User ID or system entity creating the event",
        examples=["rm_priya_01", "system_gateway"]
    )
    source: Optional[str] = Field(
        default="api",
        description="Originating system or channel",
        examples=["mobile_app", "web_portal", "core_banking", "api"]
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event data payload (e.g. deposit amount, customer holdings context, lead details)",
        examples=[{"amount": 500000.0, "customer_id": "cust_101", "currency": "INR"}]
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Tracing correlation ID shared across the full event lifecycle",
        examples=["corr_workflow_1001"]
    )
    causation_id: Optional[str] = Field(
        default=None,
        description="ID of the parent event or decision that caused this event",
        examples=["evt_prev_9002"]
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        description="Unique key ensuring duplicate requests produce exactly one business outcome",
        examples=["idemp_payin_cust101_tx9901"]
    )



class EventProcessingResult(BaseModel):
    success: bool
    event_id: str
    correlation_id: str
    decisions_made: int = 0
    actions_created: int = 0
    message: str = "Event processed successfully"
    details: Optional[Dict[str, Any]] = None
