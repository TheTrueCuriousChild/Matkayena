"""Unit tests for Canonical JSON Hashing, Cryptographic Hash Chain, and Tamper Detection."""

from backend.services.audit_blockchain_server.audit.hasher import (
    canonical_json_dumps, hash_canonical_payload, sha256_hash
)
from backend.services.audit_blockchain_server.audit.hash_chain import AuditHashChainService, GENESIS_HASH
from backend.services.shared.models import AuditRecord


def test_canonical_json_sorting_and_determinism():
    dict1 = {"b": 2, "a": 1, "nested": {"z": 26, "y": 25}}
    dict2 = {"nested": {"y": 25, "z": 26}, "a": 1, "b": 2}

    # Serialization must match character-by-character
    str1 = canonical_json_dumps(dict1)
    str2 = canonical_json_dumps(dict2)
    assert str1 == str2
    assert hash_canonical_payload(dict1) == hash_canonical_payload(dict2)


def test_hash_chain_creation_and_continuity(db_session):
    # 1. Entry 1
    rec1 = AuditHashChainService.create_audit_entry(
        db=db_session,
        entity_type="OPPORTUNITY",
        entity_id="opp_1",
        action="OPPORTUNITY_CREATED",
        payload={"score": 0.85, "title": "Insurance Cross-Sell"}
    )
    assert rec1.previous_hash == GENESIS_HASH
    assert len(rec1.current_hash) == 64

    # 2. Entry 2
    rec2 = AuditHashChainService.create_audit_entry(
        db=db_session,
        entity_type="ACTION",
        entity_id="act_1",
        action="ACTION_ASSIGNED",
        payload={"rm_id": "rm_1", "priority": "HIGH"}
    )
    assert rec2.previous_hash == rec1.current_hash
    assert len(rec2.current_hash) == 64

    # 3. Entry 3
    rec3 = AuditHashChainService.create_audit_entry(
        db=db_session,
        entity_type="COMMISSION",
        entity_id="comm_1",
        action="COMMISSION_CALCULATED",
        payload={"amount": 63250.0}
    )
    assert rec3.previous_hash == rec2.current_hash

    # Verify individual record integrity
    v1 = AuditHashChainService.verify_audit_record(db_session, rec1.id)
    assert v1["is_valid"] is True
    assert v1["payload_hash_matches"] is True
    assert v1["current_hash_matches"] is True

    # Verify full chain integrity
    chain_v = AuditHashChainService.verify_chain_integrity(db_session)
    assert chain_v["is_valid"] is True
    assert chain_v["status"] == "VERIFIED_UNBROKEN"
    assert chain_v["total_records"] >= 3


def test_tamper_detection(db_session):
    # Create valid record
    rec = AuditHashChainService.create_audit_entry(
        db=db_session,
        entity_type="TRANSACTION",
        entity_id="tx_100",
        action="PAYIN_RECEIVED",
        payload={"amount": 500000.0}
    )

    # Verify initial valid state
    v_initial = AuditHashChainService.verify_audit_record(db_session, rec.id)
    assert v_initial["is_valid"] is True

    # Mutate canonical payload in DB (tamper simulation)
    rec.canonical_payload = {"amount": 9999999.0}  # Maliciously altered
    db_session.commit()

    # Tamper detection must catch the alteration!
    v_tampered = AuditHashChainService.verify_audit_record(db_session, rec.id)
    assert v_tampered["is_valid"] is False
    assert v_tampered["payload_hash_matches"] is False
