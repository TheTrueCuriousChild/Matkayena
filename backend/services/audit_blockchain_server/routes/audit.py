"""Audit and Blockchain API endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.services.audit_blockchain_server.audit.hash_chain import AuditHashChainService
from backend.services.audit_blockchain_server.blockchain.queue import BlockchainAnchorWorker
from backend.services.shared.auth import get_current_user, require_service_auth, UserContext
from backend.services.shared.database import get_db
from backend.services.shared.repositories.audit_repo import AuditRepository

router = APIRouter(prefix="/api/v1/audit", tags=["Audit & Blockchain"])


class CreateAuditRequest(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    actor_id: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None


class AuditRecordResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: Optional[str]
    previous_hash: str
    current_hash: str
    payload_hash: str
    correlation_id: str
    causation_id: Optional[str]
    created_at: str
    blockchain_status: Optional[str] = None
    tx_hash: Optional[str] = None


@router.post("/record", status_code=status.HTTP_201_CREATED)
async def create_audit_record(
    req: CreateAuditRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_service_auth)
):
    """Creates a new canonical SHA-256 hash-chained audit record and anchors proof asynchronously."""
    audit_record = AuditHashChainService.create_audit_entry(
        db=db,
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        action=req.action,
        payload=req.payload,
        actor_id=req.actor_id or user.user_id,
        correlation_id=req.correlation_id,
        causation_id=req.causation_id
    )

    # Attempt failure-isolated blockchain anchor
    blockchain_record = await BlockchainAnchorWorker.anchor_audit_record_isolated(db, audit_record)

    return {
        "success": True,
        "audit_record_id": audit_record.id,
        "current_hash": audit_record.current_hash,
        "previous_hash": audit_record.previous_hash,
        "payload_hash": audit_record.payload_hash,
        "blockchain_status": blockchain_record.status,
        "tx_hash": blockchain_record.tx_hash,
        "blockchain_network": blockchain_record.blockchain_network
    }


@router.get("/records", response_model=List[Dict[str, Any]])
def list_audit_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Lists audit records in reverse chronological order."""
    records = AuditRepository.list_records(db, skip=skip, limit=limit)
    out = []
    for r in records:
        out.append({
            "id": r.id,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "action": r.action,
            "actor_id": r.actor_id,
            "previous_hash": r.previous_hash,
            "current_hash": r.current_hash,
            "payload_hash": r.payload_hash,
            "canonical_payload": r.canonical_payload,
            "correlation_id": r.correlation_id,
            "causation_id": r.causation_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "blockchain_status": r.blockchain_record.status if r.blockchain_record else "NOT_ANCHORED",
            "tx_hash": r.blockchain_record.tx_hash if r.blockchain_record else None
        })
    return out


@router.get("/verify/{record_id}")
def verify_audit_record(
    record_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Verifies cryptographic integrity of an individual audit record."""
    return AuditHashChainService.verify_audit_record(db, record_id)


@router.get("/verify-chain")
def verify_full_chain(
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Verifies the cryptographic continuity of the full hash chain ledger."""
    return AuditHashChainService.verify_chain_integrity(db, limit=limit)
