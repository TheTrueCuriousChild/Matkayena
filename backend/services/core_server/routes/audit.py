"""Audit and Blockchain verification proxy endpoints for Core Server."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from backend.services.shared.auth import get_current_user, require_roles, UserContext, RoleEnum
from backend.services.shared.config import settings
from backend.services.shared.http_client import ServiceClient

router = APIRouter(prefix="/api/v1/audit", tags=["Audit & Blockchain Verification"])
audit_client = ServiceClient("audit_blockchain_server", settings.AUDIT_BLOCKCHAIN_SERVER_URL)


@router.get("/records")
async def list_audit_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
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


@router.get("/verify/{record_id}")
async def verify_audit_record(
    record_id: str,
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


@router.get("/verify-chain")
async def verify_chain(
    limit: int = Query(500, ge=1, le=5000),
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
