"""Failure-isolated blockchain anchoring worker and retry queue."""

import asyncio
from typing import Optional
from sqlalchemy.orm import Session
from backend.services.audit_blockchain_server.blockchain.adapter import default_blockchain_adapter
from backend.services.shared.logging import setup_logger
from backend.services.shared.models import AuditRecord, BlockchainRecord
from backend.services.shared.repositories.audit_repo import AuditRepository

logger = setup_logger("blockchain_queue")


class BlockchainAnchorWorker:
    @staticmethod
    async def anchor_audit_record_isolated(
        db: Session,
        audit_record: AuditRecord,
        adapter=None
    ) -> BlockchainRecord:
        """Attempts to anchor an audit proof to the ledger/blockchain with strict failure isolation.

        CRITICAL: Failure will NEVER throw an exception that could interrupt business logic.
        """
        adapter = adapter or default_blockchain_adapter

        # 1. Create or fetch blockchain record in PENDING status
        b_record = BlockchainRecord(
            audit_record_id=audit_record.id,
            batch_root_hash=audit_record.current_hash,
            blockchain_network=getattr(adapter, "network", "integrity_ledger"),
            status="PENDING",
            retry_count=0
        )
        b_record = AuditRepository.create_blockchain_record(db, b_record)

        # 2. Attempt anchoring with failure isolation
        try:
            receipt = await asyncio.wait_for(
                adapter.anchor_batch(audit_record.current_hash),
                timeout=5.0
            )
            b_record = AuditRepository.update_blockchain_record(
                db=db,
                record_id=b_record.id,
                status="ANCHORED",
                tx_hash=receipt.get("tx_hash"),
                block_number=receipt.get("block_number")
            )
            logger.info(f"Audit record {audit_record.id} successfully anchored: tx={receipt.get('tx_hash')}")
        except Exception as exc:
            logger.warning(
                f"Blockchain anchoring failed for audit {audit_record.id} (status remains PENDING for retry): {exc}"
            )
            b_record = AuditRepository.update_blockchain_record(
                db=db,
                record_id=b_record.id,
                status="PENDING",
                error=str(exc)
            )

        return b_record

    @staticmethod
    async def retry_pending_anchors(db: Session, adapter=None) -> int:
        """Background process that retries failed/pending blockchain anchors."""
        adapter = adapter or default_blockchain_adapter
        pending_records = AuditRepository.get_pending_blockchain_records(db, limit=20)
        succeeded_count = 0

        for record in pending_records:
            try:
                receipt = await asyncio.wait_for(
                    adapter.anchor_batch(record.batch_root_hash),
                    timeout=5.0
                )
                AuditRepository.update_blockchain_record(
                    db=db,
                    record_id=record.id,
                    status="ANCHORED",
                    tx_hash=receipt.get("tx_hash"),
                    block_number=receipt.get("block_number")
                )
                succeeded_count += 1
            except Exception as exc:
                logger.warning(f"Retry anchoring failed for record {record.id}: {exc}")
                AuditRepository.update_blockchain_record(
                    db=db,
                    record_id=record.id,
                    status="PENDING",
                    error=str(exc)
                )

        return succeeded_count
