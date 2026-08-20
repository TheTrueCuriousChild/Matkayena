"""
Action & Workflow Service Models
----------------------------------
Tables: actions, action_history, action_outcomes
"""

import uuid

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Index, Numeric
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ──────────────────────────────────────────────
# ACTIONS
# ──────────────────────────────────────────────

class Action(Base):
    __tablename__ = "actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule_evaluation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rule_evaluations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="SET NULL"),
        nullable=True,
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
    opportunity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    achievement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("achievements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type = Column(String, nullable=False)
    priority_level = Column(String, nullable=True)
    priority_score = Column(Numeric, nullable=True)
    title = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, nullable=True, index=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    snoozed_until = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
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
    source_event = relationship("BusinessEvent", back_populates="actions")
    rule_evaluation = relationship(
        "RuleEvaluation", back_populates="actions"
    )
    rule = relationship("Rule", back_populates="actions")
    customer = relationship("Customer", back_populates="actions")
    lead = relationship("Lead", back_populates="actions")
    opportunity = relationship("Opportunity", back_populates="actions")
    achievement = relationship("Achievement", back_populates="actions")
    assignee = relationship(
        "Profile",
        foreign_keys=[assigned_to],
        back_populates="assigned_actions",
    )
    creator = relationship(
        "Profile",
        foreign_keys=[created_by],
        back_populates="created_actions",
    )

    action_history = relationship("ActionHistory", back_populates="action")
    action_outcomes = relationship("ActionOutcome", back_populates="action")


# ──────────────────────────────────────────────
# ACTION_HISTORY
# ──────────────────────────────────────────────

class ActionHistory(Base):
    __tablename__ = "action_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(
        UUID(as_uuid=True),
        ForeignKey("actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type = Column(String, nullable=False)
    previous_assignee = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    new_assignee = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    action = relationship("Action", back_populates="action_history")
    actor = relationship(
        "Profile",
        foreign_keys=[actor_id],
    )
    prev_assignee_profile = relationship(
        "Profile",
        foreign_keys=[previous_assignee],
    )
    new_assignee_profile = relationship(
        "Profile",
        foreign_keys=[new_assignee],
    )


# ──────────────────────────────────────────────
# ACTION_OUTCOMES
# ──────────────────────────────────────────────

class ActionOutcome(Base):
    __tablename__ = "action_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(
        UUID(as_uuid=True),
        ForeignKey("actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    outcome_type = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    business_value = Column(Numeric, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    next_followup_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    action = relationship("Action", back_populates="action_outcomes")
    rm = relationship("Profile", back_populates="action_outcomes")
