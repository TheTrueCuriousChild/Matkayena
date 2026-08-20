"""
Intelligence / Rule Engine Service Models
-------------------------------------------
Tables: rules, rule_versions, rule_event_types, rule_evaluations,
        opportunities, achievements
"""

import uuid

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, ForeignKey,
    Index, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ──────────────────────────────────────────────
# RULES
# ──────────────────────────────────────────────

class Rule(Base):
    __tablename__ = "rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    rule_type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    rule_versions = relationship("RuleVersion", back_populates="rule")
    rule_event_types = relationship("RuleEventType", back_populates="rule")
    opportunities = relationship("Opportunity", back_populates="source_rule")
    achievements = relationship("Achievement", back_populates="source_rule")
    actions = relationship("Action", back_populates="rule")


# ──────────────────────────────────────────────
# RULE_VERSIONS
# ──────────────────────────────────────────────

class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    conditions = Column(JSONB, nullable=True)
    action_config = Column(JSONB, nullable=True)
    scoring_config = Column(JSONB, nullable=True)
    event_window_minutes = Column(Integer, nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    rule = relationship("Rule", back_populates="rule_versions")
    rule_evaluations = relationship(
        "RuleEvaluation", back_populates="rule_version"
    )


# ──────────────────────────────────────────────
# RULE_EVENT_TYPES  (composite PK junction table)
# ──────────────────────────────────────────────

class RuleEventType(Base):
    __tablename__ = "rule_event_types"

    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="CASCADE"),
        primary_key=True,
    )
    event_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("event_types.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    rule = relationship("Rule", back_populates="rule_event_types")
    event_type = relationship(
        "EventType", back_populates="rule_event_types"
    )


# ──────────────────────────────────────────────
# RULE_EVALUATIONS
# ──────────────────────────────────────────────

class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rule_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
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
    matched = Column(Boolean, nullable=False)
    score = Column(Numeric, nullable=True)
    evaluated_state = Column(JSONB, nullable=True)
    matched_conditions = Column(JSONB, nullable=True)
    explanation = Column(Text, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rule_version = relationship(
        "RuleVersion", back_populates="rule_evaluations"
    )
    event = relationship(
        "BusinessEvent", back_populates="rule_evaluations"
    )
    customer = relationship("Customer", back_populates="rule_evaluations")
    lead = relationship("Lead", back_populates="rule_evaluations")
    rm = relationship("Profile", back_populates="rule_evaluations")
    actions = relationship("Action", back_populates="rule_evaluation")


# ──────────────────────────────────────────────
# OPPORTUNITIES
# ──────────────────────────────────────────────

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    opportunity_type = Column(String, nullable=True)
    status = Column(String, nullable=True, index=True)
    potential_value = Column(Numeric, nullable=True)
    score = Column(Numeric, nullable=True)
    reason = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    customer = relationship("Customer", back_populates="opportunities")
    lead = relationship("Lead", back_populates="opportunities")
    rm = relationship("Profile", back_populates="opportunities")
    product = relationship("Product", back_populates="opportunities")
    source_event = relationship(
        "BusinessEvent", back_populates="opportunities"
    )
    source_rule = relationship("Rule", back_populates="opportunities")
    actions = relationship("Action", back_populates="opportunity")


# ──────────────────────────────────────────────
# ACHIEVEMENTS
# ──────────────────────────────────────────────

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    achievement_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    achieved_value = Column(Numeric, nullable=True)
    target_value = Column(Numeric, nullable=True)
    achieved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    rm = relationship("Profile", back_populates="achievements")
    source_event = relationship(
        "BusinessEvent", back_populates="achievements"
    )
    source_rule = relationship("Rule", back_populates="achievements")
    actions = relationship("Action", back_populates="achievement")
