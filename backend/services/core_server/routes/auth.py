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


class RegisterRequest(BaseModel):
    user_id: Optional[str] = Field(
        default=None,
        description="Optional specific user/profile ID. If omitted, a unique UUID is generated.",
        examples=["rm_priya_01", "mgr_vikram_01"]
    )
    employee_code: Optional[str] = Field(
        default=None,
        description="Employee code / Staff ID",
        examples=["EMP-8821"]
    )
    full_name: str = Field(
        ...,
        description="Full legal name of the user",
        examples=["Priya Sharma", "Vikram Seth"]
    )
    email: str = Field(
        ...,
        description="Work email address",
        examples=["priya.sharma@matkayena.com", "vikram.seth@matkayena.com"]
    )
    phone: Optional[str] = Field(
        default=None,
        description="Contact phone number",
        examples=["+91-9876543210"]
    )
    roles: List[str] = Field(
        default=[RoleEnum.RM.value],
        description="Assigned role(s): RM, TEAM_LEAD, MANAGER, REGIONAL_MANAGER, ADMIN",
        examples=[["RM"], ["MANAGER"], ["ADMIN"]]
    )
    manager_id: Optional[str] = Field(
        default=None,
        description="User ID of reporting manager (for RMs)",
        examples=["mgr_vikram_01"]
    )
    org_unit_id: Optional[str] = Field(
        default="branch_mumbai_01",
        description="Branch or Organizational Unit ID",
        examples=["branch_mumbai_01"]
    )


class RegisterResponse(BaseModel):
    user_id: str = Field(description="Unique profile user ID")
    full_name: str = Field(description="Full name")
    email: str = Field(description="Registered email")
    roles: List[str] = Field(description="Assigned roles")
    manager_id: Optional[str] = Field(description="Assigned manager ID")
    org_unit_id: Optional[str] = Field(description="Branch / Org Unit")
    access_token: str = Field(description="Instant JWT Bearer token for immediate API testing")
    token_type: str = Field(default="bearer")
    message: str = Field(default="User profile registered successfully.")


from fastapi import Depends
from sqlalchemy.orm import Session
from backend.services.shared.database import get_db
from backend.services.shared.models import Profile


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User & Issue Token",
    description="Registers a new RM, Manager, or Admin profile in the database and returns an immediate JWT token."
)
@router.post(
    "/register-user",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User & Issue Token (Descriptive Alias)",
    description="Registers a new RM, Manager, or Admin profile in the database and returns an immediate JWT token."
)
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a user profile and returns instant authentication token."""
    import uuid
    user_id = req.user_id or str(uuid.uuid4())
    
    # Upsert Profile
    existing = db.query(Profile).filter(Profile.email == req.email).first()
    if existing:
        existing.full_name = req.full_name
        existing.phone = req.phone
        existing.manager_id = req.manager_id
        existing.org_unit_id = req.org_unit_id
        if req.employee_code:
            existing.employee_code = req.employee_code
        db.commit()
        db.refresh(existing)
        profile = existing
        user_id = existing.id
    else:
        profile = Profile(
            id=user_id,
            employee_code=req.employee_code or f"EMP-{user_id[:6].upper()}",
            full_name=req.full_name,
            email=req.email,
            phone=req.phone,
            manager_id=req.manager_id,
            org_unit_id=req.org_unit_id,
            is_active=True
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    token = create_access_token(
        user_id=user_id,
        email=req.email,
        roles=req.roles,
        org_unit_id=req.org_unit_id
    )

    return RegisterResponse(
        user_id=user_id,
        full_name=profile.full_name,
        email=profile.email,
        roles=req.roles,
        manager_id=profile.manager_id,
        org_unit_id=profile.org_unit_id,
        access_token=token,
        message="User profile registered and JWT access token issued successfully."
    )


class LoginRequest(BaseModel):
    email: str = Field(
        ...,
        description="Registered work email address of user",
        examples=["priya.sharma@matkayena.com", "vikram.seth@matkayena.com"]
    )
    password: Optional[str] = Field(
        default=None,
        description="User password (optional / placeholder for standard auth flow)",
        examples=["SecurePass123!"]
    )
    roles: Optional[List[str]] = Field(
        default=None,
        description="Optional roles to grant if logging in directly",
        examples=[["RM"], ["MANAGER"]]
    )


class LoginResponse(BaseModel):
    user_id: str = Field(description="Unique profile user ID")
    full_name: str = Field(description="Full name")
    email: str = Field(description="User email")
    roles: List[str] = Field(description="Active user roles")
    manager_id: Optional[str] = Field(description="Manager ID")
    org_unit_id: Optional[str] = Field(description="Branch ID")
    access_token: str = Field(description="Signed JWT access token for API authorization")
    token_type: str = Field(default="bearer")
    message: str = Field(default="Login successful.")


from backend.services.shared.auth import get_current_user, UserContext


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login User & Retrieve Token",
    description="Authenticates user by email, retrieves profile from database, and issues signed JWT access token."
)
@router.post(
    "/login-user",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login User & Retrieve Token (Descriptive Alias)",
    description="Authenticates user by email, retrieves profile from database, and issues signed JWT access token."
)
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    """Logs in an existing user or auto-resolves profile to issue JWT token."""
    profile = db.query(Profile).filter(Profile.email == req.email).first()
    
    if not profile:
        # Fallback profile creation for immediate testing
        user_id = f"user_{req.email.split('@')[0]}"
        profile = Profile(
            id=user_id,
            employee_code=f"EMP-{user_id[:6].upper()}",
            full_name=req.email.split('@')[0].replace('.', ' ').title(),
            email=req.email,
            org_unit_id="branch_mumbai_01",
            is_active=True
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    roles = req.roles or ["MANAGER" if "mgr" in profile.id or "manager" in req.email.lower() else "RM"]

    token = create_access_token(
        user_id=profile.id,
        email=profile.email,
        roles=roles,
        org_unit_id=profile.org_unit_id
    )

    return LoginResponse(
        user_id=profile.id,
        full_name=profile.full_name,
        email=profile.email,
        roles=roles,
        manager_id=profile.manager_id,
        org_unit_id=profile.org_unit_id,
        access_token=token,
        message="Login successful. Use this access_token in 'Authorize' button or 'Authorization: Bearer <token>' header."
    )


@router.get(
    "/me",
    summary="Get Current Authenticated User Profile",
    description="Decodes the current JWT Bearer token and returns profile and role claims."
)
@router.get(
    "/current-user",
    summary="Get Current Authenticated User Profile (Descriptive Alias)",
    description="Decodes the current JWT Bearer token and returns profile and role claims."
)
def get_current_user_profile(user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns context and DB profile of the currently logged-in user."""
    profile = db.query(Profile).filter(Profile.id == user.user_id).first()
    return {
        "user_id": user.user_id,
        "email": user.email,
        "roles": user.roles,
        "org_unit_id": user.org_unit_id,
        "full_name": profile.full_name if profile else user.email.split('@')[0].title(),
        "manager_id": profile.manager_id if profile else None,
        "is_active": profile.is_active if profile else True
    }



