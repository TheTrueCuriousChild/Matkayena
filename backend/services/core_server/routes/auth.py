"""Authentication and Token Issuance Endpoint."""

from typing import List, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel
from backend.services.shared.auth import create_access_token, RoleEnum

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class TokenRequest(BaseModel):
    user_id: str
    email: str
    roles: List[str] = [RoleEnum.RM.value]
    org_unit_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    roles: List[str]


@router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def generate_token(req: TokenRequest):
    """Issues a signed JWT token for the user."""
    token = create_access_token(
        user_id=req.user_id,
        email=req.email,
        roles=req.roles,
        org_unit_id=req.org_unit_id
    )
    return TokenResponse(
        access_token=token,
        user_id=req.user_id,
        email=req.email,
        roles=req.roles
    )
