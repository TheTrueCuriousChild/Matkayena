"""Unit tests for Blockchain Adapter and Failure Isolation."""

import pytest
from backend.services.audit_blockchain_server.blockchain.adapter import LocalIntegrityLedgerAdapter, BlockchainAdapter
from backend.services.audit_blockchain_server.blockchain.queue import BlockchainAnchorWorker
from backend.services.audit_blockchain_server.audit.hash_chain import AuditHashChainService
from backend.services.shared.models import BlockchainRecord


class FailingMockBlockchainAdapter(BlockchainAdapter):
    """Simulates an unavailable or crashed blockchain RPC node."""
    async def anchor_batch(self, batch_root_hash: str):
        raise ConnectionError("Blockchain RPC Gateway Timeout 504 (Node Offline)")

    async def verify_anchor(self, tx_hash: str):
        raise ConnectionError("Blockchain unavailable")

    async def get_anchor_status(self, tx_hash: str):
        raise ConnectionError("Blockchain unavailable")


@pytest.mark.asyncio
async def test_local_integrity_ledger_anchoring():
    adapter = LocalIntegrityLedgerAdapter()
    root_hash = "a" * 64

    receipt = await adapter.anchor_batch(root_hash)
    assert receipt["status"] == "ANCHORED"
    assert receipt["network"] == "local_integrity_ledger"
    assert receipt["batch_root_hash"] == root_hash
    assert receipt["tx_hash"].startswith("0x")

    verification = await adapter.verify_anchor(receipt["tx_hash"])
    assert verification["is_verified"] is True
    assert verification["block_number"] == receipt["block_number"]


@pytest.mark.asyncio
async def test_blockchain_failure_isolation(db_session):
    """CRITICAL REQUIREMENT:

    When blockchain is offline/unreachable, normal business operations and audit records
    MUST NOT fail or roll back! The blockchain status becomes PENDING for background retry.
    """
    # 1. Create audit record
    audit_rec = AuditHashChainService.create_audit_entry(
        db=db_session,
        entity_type="ACTION",
        entity_id="act_isolated_1",
        action="CONVERSION_COMPLETED",
        payload={"value": 1000000.0}
    )
    assert audit_rec is not None

    # 2. Attempt anchoring with a failing blockchain adapter
    failing_adapter = FailingMockBlockchainAdapter()
    blockchain_rec = await BlockchainAnchorWorker.anchor_audit_record_isolated(
        db=db_session,
        audit_record=audit_rec,
        adapter=failing_adapter
    )

    # 3. Verify audit record is unaffected and blockchain record is marked PENDING with error
    assert blockchain_rec.status == "PENDING"
    assert "Timeout" in blockchain_rec.last_error
    assert blockchain_rec.retry_count == 1
    assert audit_rec.id is not None
