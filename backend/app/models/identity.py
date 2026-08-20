"""
Identity & Organization Service Models
---------------------------------------
Tables: roles, org_units, profiles, user_roles
"""

import uuid

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ──────────────────────────────────────────────
# ROLES
# ──────────────────────────────────────────────

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user_roles = relationship("UserRole", back_populates="role")


# ──────────────────────────────────────────────
# ORG_UNITS  (self-referencing hierarchy)
# ──────────────────────────────────────────────

class OrgUnit(Base):
    __tablename__ = "org_units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    unit_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Self-referencing relationship
    parent = relationship(
        "OrgUnit",
        remote_side="OrgUnit.id",
        back_populates="children",
    )
    children = relationship(
        "OrgUnit",
        back_populates="parent",
    )

    # Relationships to other services
    profiles = relationship("Profile", back_populates="org_unit")
    targets = relationship("Target", back_populates="org_unit")
    benchmarks = relationship("Benchmark", back_populates="org_unit")


# ──────────────────────────────────────────────
# PROFILES  (self-referencing manager hierarchy)
# ──────────────────────────────────────────────

class Profile(Base):
    __tablename__ = "profiles"

    # PK is also an FK referencing Supabase auth.users (external)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_code = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    org_unit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Self-referencing relationship  (manager)
    manager = relationship(
        "Profile",
        remote_side="Profile.id",
        back_populates="direct_reports",
    )
    direct_reports = relationship(
        "Profile",
        back_populates="manager",
    )

    # Org unit
    org_unit = relationship("OrgUnit", back_populates="profiles")

    # Junction table
    user_roles = relationship("UserRole", back_populates="profile")

    # CRM relationships
    customers = relationship("Customer", back_populates="rm")
    leads = relationship("Lead", back_populates="rm")
    interactions = relationship("Interaction", back_populates="rm")
    transactions = relationship("Transaction", back_populates="rm")

    # Event relationships
    business_events = relationship("BusinessEvent", back_populates="rm")

    # Intelligence relationships
    rule_evaluations = relationship("RuleEvaluation", back_populates="rm")
    opportunities = relationship("Opportunity", back_populates="rm")
    achievements = relationship("Achievement", back_populates="rm")

    # Action relationships
    assigned_actions = relationship(
        "Action",
        foreign_keys="Action.assigned_to",
        back_populates="assignee",
    )
    created_actions = relationship(
        "Action",
        foreign_keys="Action.created_by",
        back_populates="creator",
    )
    action_outcomes = relationship("ActionOutcome", back_populates="rm")

    # Performance relationships
    targets = relationship("Target", back_populates="rm")
    performance_snapshots = relationship(
        "RmPerformanceSnapshot", back_populates="rm"
    )

    # Audit relationships
    audit_records = relationship("AuditRecord", back_populates="actor")

    __table_args__ = (
        Index("ix_profiles_email", "email"),
    )


# ──────────────────────────────────────────────
# USER_ROLES  (composite PK junction table)
# ──────────────────────────────────────────────

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    profile = relationship("Profile", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
