"""Authentication and Token Issuance Endpoint."""

from typing import List, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from backend.services.shared.auth import create_access_token, RoleEnum


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class TokenRequest(BaseModel):
    user_id: str = Field(
        ...,
        description="Unique user identifier",
        examples=["rm_priya_01", "mgr_vikram_01", "admin_user"]
    )
    email: str = Field(
        ...,
        description="Email address associated with the user profile",
        examples=["priya@matkayena.com", "vikram@matkayena.com"]
    )
    roles: List[str] = Field(
        default=[RoleEnum.RM.value],
        description="Assigned role(s) for RBAC authorization: RM, TEAM_LEAD, MANAGER, REGIONAL_MANAGER, ADMIN, SYSTEM_SERVICE",
        examples=[["RM"], ["MANAGER"], ["ADMIN"]]
    )
    org_unit_id: Optional[str] = Field(
        default=None,
        description="Optional organizational unit/branch ID",
        examples=["branch_mumbai_01"]
    )


class TokenResponse(BaseModel):
    access_token: str = Field(description="JWT bearer token to pass in 'Authorization: Bearer <token>' header")
    token_type: str = Field(default="bearer", description="Token scheme type")
    user_id: str = Field(description="Authenticated user ID")
    email: str = Field(description="User email")
    roles: List[str] = Field(description="List of granted roles")


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate JWT Authentication Token",
    description="Issues a signed JWT access token containing user roles and permissions for API testing."
)
@router.post(
    "/generate-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate JWT Authentication Token (Descriptive Alias)",
    description="Issues a signed JWT access token containing user roles and permissions for API testing."
)
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

