"""Audit and Blockchain API endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.services.audit_blockchain_server.audit.hash_chain import AuditHashChainService
from backend.services.audit_blockchain_server.blockchain.queue import BlockchainAnchorWorker
from backend.services.shared.auth import get_current_user, require_service_auth, UserContext
from backend.services.shared.database import get_db
from backend.services.shared.repositories.audit_repo import AuditRepository

router = APIRouter(prefix="/api/v1/audit", tags=["Audit & Blockchain"])


class CreateAuditRequest(BaseModel):
    entity_type: str = Field(
        ...,
        description="Type of entity audited (e.g. OPPORTUNITY, ACTION, COMMISSION, TRANSACTION)",
        examples=["ACTION", "COMMISSION"]
    )
    entity_id: str = Field(
        ...,
        description="Unique ID of the audited entity",
        examples=["act_101", "comm_501"]
    )
    action: str = Field(
        ...,
        description="Action performed (e.g. OPPORTUNITY_CREATED, ACTION_COMPLETED, COMMISSION_CALCULATED)",
        examples=["ACTION_COMPLETED", "COMMISSION_CALCULATED"]
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Canonical data payload to be deterministically hashed with SHA-256",
        examples=[{"converted_value": 500000.0, "commission_amount": 32812.5, "rm_id": "rm_priya_01"}]
    )
    actor_id: Optional[str] = Field(
        default=None,
        description="User or system service that performed the action",
        examples=["rm_priya_01", "system_engine"]
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Tracing correlation ID for end-to-end audit tracking",
        examples=["corr_workflow_1001"]
    )
    causation_id: Optional[str] = Field(
        default=None,
        description="Causal event or decision identifier"
    )


class AuditRecordResponse(BaseModel):
    id: str = Field(description="Unique audit record ID")
    entity_type: str = Field(description="Audited entity type")
    entity_id: str = Field(description="Audited entity ID")
    action: str = Field(description="Action name")
    actor_id: Optional[str] = Field(description="Actor ID")
    previous_hash: str = Field(description="SHA-256 hash of the preceding block (or Genesis)")
    current_hash: str = Field(description="SHA-256 hash of the current node")
    payload_hash: str = Field(description="SHA-256 hash of the canonical JSON payload")
    correlation_id: str = Field(description="Tracing correlation ID")
    causation_id: Optional[str] = Field(description="Causation ID")
    created_at: str = Field(description="Timestamp of audit record creation")
    blockchain_status: Optional[str] = Field(default=None, description="ANCHORED, PENDING, or FAILED")
    tx_hash: Optional[str] = Field(default=None, description="Blockchain transaction proof hash")


@router.post(
    "/record",
    status_code=status.HTTP_201_CREATED,
    summary="Record Immutable Audit Entry",
    description="Creates a canonical SHA-256 hash-chain entry and queues isolated blockchain anchoring."
)
@router.post(
    "/create-record",
    status_code=status.HTTP_201_CREATED,
    summary="Record Immutable Audit Entry (Descriptive Alias)",
    description="Creates a canonical SHA-256 hash-chain entry and queues isolated blockchain anchoring."
)
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


@router.get(
    "/records",
    response_model=List[AuditRecordResponse],
    summary="List Audit Records with Blockchain Proofs",
    description="Retrieves chronological audit entries with their SHA-256 node hashes and blockchain anchor proofs."
)
@router.get(
    "/list-records",
    response_model=List[AuditRecordResponse],
    summary="List Audit Records (Descriptive Alias)",
    description="Retrieves chronological audit entries with their SHA-256 node hashes and blockchain anchor proofs."
)
def list_audit_records(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max audit entries to retrieve"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type: OPPORTUNITY, ACTION, COMMISSION"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    records = AuditRepository.list_records(db, skip=skip, limit=limit, entity_type=entity_type)
    result = []
    for r in records:
        b_rec = AuditRepository.get_blockchain_record_by_audit_id(db, r.id)
        result.append(
            AuditRecordResponse(
                id=r.id,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                action=r.action,
                actor_id=r.actor_id,
                previous_hash=r.previous_hash,
                current_hash=r.current_hash,
                payload_hash=r.payload_hash,
                correlation_id=r.correlation_id,
                causation_id=r.causation_id,
                created_at=r.created_at.isoformat() if r.created_at else "",
                blockchain_status=b_rec.status if b_rec else None,
                tx_hash=b_rec.tx_hash if b_rec else None
            )
        )
    return result


@router.get(
    "/verify/{record_id}",
    summary="Verify Individual Audit Record Cryptographic Proof",
    description="Recomputes the canonical JSON payload SHA-256 and node hash to verify record integrity."
)
@router.get(
    "/verify-record/{record_id}",
    summary="Verify Audit Record (Descriptive Alias)",
    description="Recomputes the canonical JSON payload SHA-256 and node hash to verify record integrity."
)
def verify_audit_record(
    record_id: str = Path(..., description="Unique Audit Record identifier to verify", examples=["aud_101"]),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    return AuditHashChainService.verify_audit_record(db, record_id)



@router.get(
    "/verify-chain",
    summary="Verify Full Cryptographic Hash-Chain Integrity",
    description="Validates that every node from Genesis (0000...) to the latest block is continuous and untampered."
)
@router.get(
    "/verify-full-chain",
    summary="Verify Full Hash Chain (Descriptive Alias)",
    description="Validates that every node from Genesis (0000...) to the latest block is continuous and untampered."
)
def verify_chain_integrity(
    limit: int = Query(500, ge=1, le=5000, description="Max block depth to verify"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    return AuditHashChainService.verify_chain_integrity(db, limit=limit)
