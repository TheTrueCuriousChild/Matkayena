"""Cryptographic hash-chain service for tamper-evident audit records."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.services.audit_blockchain_server.audit.hasher import (
    calculate_current_hash, hash_canonical_payload
)
from backend.services.shared.models import AuditRecord
from backend.services.shared.repositories.audit_repo import AuditRepository

GENESIS_HASH = "0" * 64


class AuditHashChainService:
    @classmethod
    def create_audit_entry(
        cls,
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: Dict[str, Any],
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> AuditRecord:
        """Appends a new immutable tamper-evident record to the cryptographic hash chain."""
        # 1. Fetch previous record to get previous_hash
        last_record = AuditRepository.get_last_record(db)
        previous_hash = last_record.current_hash if last_record else GENESIS_HASH

        # 2. Canonical payload hash
        payload_hash = hash_canonical_payload(payload)

        # 3. Timestamp
        now = datetime.now(timezone.utc)
        created_at_iso = now.isoformat()

        # 4. Hash-chain node calculation
        current_hash = calculate_current_hash(
            previous_hash=previous_hash,
            payload_hash=payload_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action
        )

        # 5. Persist record
        audit_record = AuditRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            previous_hash=previous_hash,
            current_hash=current_hash,
            payload_hash=payload_hash,
            canonical_payload=payload,
            correlation_id=correlation_id or "root",
            causation_id=causation_id,
            created_at=now
        )
        return AuditRepository.create_record(db, audit_record)

    @classmethod
    def verify_audit_record(cls, db: Session, record_id: str) -> Dict[str, Any]:
        """Verifies if a specific record's payload hash and current hash match its contents."""
        record = AuditRepository.get_by_id(db, record_id)
        if not record:
            return {"is_valid": False, "error": f"Record {record_id} not found"}

        # Re-verify payload hash
        expected_payload_hash = hash_canonical_payload(record.canonical_payload)
        payload_valid = (expected_payload_hash == record.payload_hash)

        # Re-verify current hash
        expected_current_hash = calculate_current_hash(
            previous_hash=record.previous_hash,
            payload_hash=record.payload_hash,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            action=record.action
        )
        current_valid = (expected_current_hash == record.current_hash)

        return {
            "record_id": record.id,
            "is_valid": payload_valid and current_valid,
            "payload_hash_matches": payload_valid,
            "current_hash_matches": current_valid,
            "current_hash": record.current_hash,
            "previous_hash": record.previous_hash,
            "timestamp": record.created_at.isoformat() if record.created_at else None
        }

    @classmethod
    def verify_chain_integrity(cls, db: Session, limit: int = 500) -> Dict[str, Any]:
        """Verifies the unbroken cryptographic continuity across the entire audit log."""
        records: List[AuditRecord] = AuditRepository.list_chain(db, limit=limit)
        if not records:
            return {"is_valid": True, "total_records": 0, "status": "EMPTY_LEDGER"}

        expected_prev_hash = GENESIS_HASH
        for idx, record in enumerate(records):
            if record.previous_hash != expected_prev_hash:
                return {
                    "is_valid": False,
                    "tamper_detected_at_index": idx,
                    "record_id": record.id,
                    "expected_previous_hash": expected_prev_hash,
                    "actual_previous_hash": record.previous_hash,
                    "status": "CHAIN_BROKEN"
                }

            # Verify integrity of this node
            node_verification = cls.verify_audit_record(db, record.id)
            if not node_verification["is_valid"]:
                return {
                    "is_valid": False,
                    "tamper_detected_at_index": idx,
                    "record_id": record.id,
                    "status": "RECORD_CONTENT_TAMPERED",
                    "details": node_verification
                }

            expected_prev_hash = record.current_hash

        return {
            "is_valid": True,
            "total_records": len(records),
            "latest_root_hash": records[-1].current_hash,
            "status": "VERIFIED_UNBROKEN"
        }
