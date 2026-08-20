"""Repository for Audit Records and Blockchain Records."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import AuditRecord, BlockchainRecord


class AuditRepository:
    @staticmethod
    def get_last_record(db: Session) -> Optional[AuditRecord]:
        """Gets the most recent audit record to fetch the previous_hash for the hash chain."""
        return db.query(AuditRecord).order_by(AuditRecord.created_at.desc()).first()

    @staticmethod
    def create_record(db: Session, record: AuditRecord) -> AuditRecord:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_by_id(db: Session, record_id: str) -> Optional[AuditRecord]:
        return db.query(AuditRecord).filter(AuditRecord.id == record_id).first()

    @staticmethod
    def list_records(db: Session, skip: int = 0, limit: int = 100) -> List[AuditRecord]:
        return db.query(AuditRecord).order_by(AuditRecord.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def list_chain(db: Session, limit: int = 100) -> List[AuditRecord]:
        return db.query(AuditRecord).order_by(AuditRecord.created_at.asc()).limit(limit).all()

    @staticmethod
    def create_blockchain_record(db: Session, record: BlockchainRecord) -> BlockchainRecord:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_pending_blockchain_records(db: Session, limit: int = 50) -> List[BlockchainRecord]:
        return db.query(BlockchainRecord).filter(
            BlockchainRecord.status.in_(["PENDING", "FAILED"]),
            BlockchainRecord.retry_count < 5
        ).order_by(BlockchainRecord.created_at.asc()).limit(limit).all()

    @staticmethod
    def update_blockchain_record(
        db: Session,
        record_id: str,
        status: str,
        tx_hash: Optional[str] = None,
        block_number: Optional[int] = None,
        error: Optional[str] = None
    ) -> Optional[BlockchainRecord]:
        record = db.query(BlockchainRecord).filter(BlockchainRecord.id == record_id).first()
        if record:
            record.status = status
            if tx_hash:
                record.tx_hash = tx_hash
            if block_number:
                record.block_number = block_number
            if error:
                record.last_error = error
                record.retry_count += 1
            if status == "ANCHORED":
                record.anchored_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(record)
        return record
