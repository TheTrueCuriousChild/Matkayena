"""
Audit / Blockchain Service Models
------------------------------------
Tables: audit_records, blockchain_records
"""

import uuid

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ──────────────────────────────────────────────
# AUDIT_RECORDS
# ──────────────────────────────────────────────

class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String, nullable=False)
    before_state = Column(JSONB, nullable=True)
    after_state = Column(JSONB, nullable=True)
    record_hash = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    actor = relationship("Profile", back_populates="audit_records")
    blockchain_records = relationship(
        "BlockchainRecord", back_populates="audit_record"
    )

    __table_args__ = (
        Index("ix_audit_records_entity", "entity_type", "entity_id"),
    )


# ──────────────────────────────────────────────
# BLOCKCHAIN_RECORDS
# ──────────────────────────────────────────────

class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    network = Column(String, nullable=True)
    contract_address = Column(String, nullable=True)
    transaction_hash = Column(String, unique=True, nullable=False)
    block_number = Column(String, nullable=True)
    record_hash = Column(String, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    status = Column(String, nullable=True, index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # FK to audit_records — ER schema: AUDIT_RECORDS ||--o{ BLOCKCHAIN_RECORDS
    # entity_id + entity_type form a logical reference; we also add a direct FK
    # via a nullable audit_record_id for the "notarized by" relationship.
    audit_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audit_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    audit_record = relationship(
        "AuditRecord", back_populates="blockchain_records"
    )
