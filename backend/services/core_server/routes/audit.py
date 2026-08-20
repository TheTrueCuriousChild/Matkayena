"""Audit and Blockchain verification proxy endpoints for Core Server."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, Request, status
from backend.services.shared.auth import get_current_user, require_roles, UserContext, RoleEnum
from backend.services.shared.config import settings
from backend.services.shared.http_client import ServiceClient

router = APIRouter(prefix="/api/v1/audit", tags=["Audit & Blockchain Verification"])
audit_client = ServiceClient("audit_blockchain_server", settings.AUDIT_BLOCKCHAIN_SERVER_URL)


@router.get(
    "/records",
    summary="List Cryptographic Audit Records",
    description="Retrieves immutable SHA-256 hash records in reverse chronological order."
)
@router.get(
    "/records/list-records",
    summary="List Audit Records (Descriptive Alias)",
    description="Retrieves immutable SHA-256 hash records in reverse chronological order."
)
async def list_audit_records(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Number of audit records to return"),
    request: Request = None,
    user: UserContext = Depends(require_roles([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]))
):
    correlation_id = getattr(request.state, "correlation_id", None) if request else None
    request_id = getattr(request.state, "request_id", None) if request else None

    return await audit_client.get(
        endpoint="/api/v1/audit/records",
        params={"skip": skip, "limit": limit},
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )


@router.get(
    "/verify/{record_id}",
    summary="Verify Audit Record Proof",
    description="Cryptographically verifies that the payload hash and node hash match stored data."
)
@router.get(
    "/verify-record/{record_id}",
    summary="Verify Audit Record Proof (Descriptive Alias)",
    description="Cryptographically verifies that the payload hash and node hash match stored data."
)
async def verify_audit_record(
    record_id: str = Path(..., description="Unique Audit Record identifier to verify", examples=["aud_101"]),
    request: Request = None,
    user: UserContext = Depends(get_current_user)
):

    correlation_id = getattr(request.state, "correlation_id", None) if request else None
    request_id = getattr(request.state, "request_id", None) if request else None

    return await audit_client.get(
        endpoint=f"/api/v1/audit/verify/{record_id}",
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )


@router.get(
    "/verify-chain",
    summary="Verify Full Hash-Chain Continuity",
    description="Traverses from Genesis hash to the latest root block to prove the entire ledger is untampered."
)
@router.get(
    "/verify-chain/validate-ledger",
    summary="Verify Full Hash Chain (Descriptive Alias)",
    description="Traverses from Genesis hash to the latest root block to prove the entire ledger is untampered."
)
async def verify_chain(
    limit: int = Query(500, ge=1, le=5000, description="Max block depth to verify"),
    request: Request = None,
    user: UserContext = Depends(require_roles([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]))
):

    correlation_id = getattr(request.state, "correlation_id", None) if request else None
    request_id = getattr(request.state, "request_id", None) if request else None

    return await audit_client.get(
        endpoint="/api/v1/audit/verify-chain",
        params={"limit": limit},
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )
