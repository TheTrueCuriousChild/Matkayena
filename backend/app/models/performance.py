"""
Performance Intelligence Service Models
-----------------------------------------
Tables: targets, benchmarks, rm_performance_snapshots
"""

import uuid

from sqlalchemy import (
    Column, String, Boolean, Integer, Date, DateTime, ForeignKey,
    Index, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ──────────────────────────────────────────────
# TARGETS
# ──────────────────────────────────────────────

class Target(Base):
    __tablename__ = "targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rm_id = Column(
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
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metric_code = Column(String, nullable=False)
    period_type = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    target_value = Column(Numeric, nullable=False)
    unit = Column(String, nullable=True)
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

    # Relationships
    rm = relationship("Profile", back_populates="targets")
    org_unit = relationship("OrgUnit", back_populates="targets")
    product = relationship("Product", back_populates="targets")

    __table_args__ = (
        Index("ix_targets_metric_code", "metric_code"),
        Index("ix_targets_period", "period_start", "period_end"),
    )


# ──────────────────────────────────────────────
# BENCHMARKS
# ──────────────────────────────────────────────

class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_unit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metric_code = Column(String, nullable=False)
    benchmark_type = Column(String, nullable=False)
    benchmark_value = Column(Numeric, nullable=False)
    unit = Column(String, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    org_unit = relationship("OrgUnit", back_populates="benchmarks")
    product = relationship("Product", back_populates="benchmarks")

    __table_args__ = (
        Index("ix_benchmarks_metric_code", "metric_code"),
    )


# ──────────────────────────────────────────────
# RM_PERFORMANCE_SNAPSHOTS
# ──────────────────────────────────────────────

class RmPerformanceSnapshot(Base):
    __tablename__ = "rm_performance_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_date = Column(Date, nullable=False)
    target_value = Column(Numeric, nullable=True)
    achieved_value = Column(Numeric, nullable=True)
    achievement_percent = Column(Numeric, nullable=True)
    expected_run_rate_percent = Column(Numeric, nullable=True)
    conversion_rate = Column(Numeric, nullable=True)
    activity_count = Column(Integer, nullable=True)
    overdue_action_count = Column(Integer, nullable=True)
    pipeline_value = Column(Numeric, nullable=True)
    sla_breach_count = Column(Numeric, nullable=True)
    contributing_factors = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    rm = relationship("Profile", back_populates="performance_snapshots")

    __table_args__ = (
        Index(
            "ix_rm_performance_snapshots_date",
            "rm_id",
            "snapshot_date",
        ),
    )
