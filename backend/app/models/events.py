"""
Event Processing Service Models
---------------------------------
Tables: event_types, business_events, event_processing_attempts
"""

import uuid

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, ForeignKey,
    Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ──────────────────────────────────────────────
# EVENT_TYPES
# ──────────────────────────────────────────────

class EventType(Base):
    __tablename__ = "event_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    schema_definition = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    business_events = relationship(
        "BusinessEvent", back_populates="event_type"
    )
    rule_event_types = relationship(
        "RuleEventType", back_populates="event_type"
    )


# ──────────────────────────────────────────────
# BUSINESS_EVENTS
# ──────────────────────────────────────────────

class BusinessEvent(Base):
    __tablename__ = "business_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("event_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_key = Column(String, unique=True, nullable=False)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    lead_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payload = Column(JSONB, nullable=True)
    source = Column(String, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    processing_status = Column(String, nullable=True, index=True)
    retry_count = Column(Integer, default=0, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    event_type = relationship("EventType", back_populates="business_events")
    customer = relationship("Customer", back_populates="business_events")
    lead = relationship("Lead", back_populates="business_events")
    rm = relationship("Profile", back_populates="business_events")
    transaction = relationship(
        "Transaction", back_populates="business_events"
    )

    processing_attempts = relationship(
        "EventProcessingAttempt", back_populates="event"
    )
    rule_evaluations = relationship(
        "RuleEvaluation", back_populates="event"
    )
    opportunities = relationship(
        "Opportunity", back_populates="source_event"
    )
    achievements = relationship(
        "Achievement", back_populates="source_event"
    )
    actions = relationship("Action", back_populates="source_event")


# ──────────────────────────────────────────────
# EVENT_PROCESSING_ATTEMPTS
# ──────────────────────────────────────────────

class EventProcessingAttempt(Base):
    __tablename__ = "event_processing_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String, nullable=True)
    attempt_number = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    event = relationship(
        "BusinessEvent", back_populates="processing_attempts"
    )
