"""Authentication, JWT token verification, and RBAC authorization."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Set
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel
from backend.services.shared.config import settings
from backend.services.shared.errors import AuthenticationError, AuthorizationError


class RoleEnum(str, Enum):
    RM = "RM"
    TEAM_LEAD = "TEAM_LEAD"
    MANAGER = "MANAGER"
    REGIONAL_MANAGER = "REGIONAL_MANAGER"
    ADMIN = "ADMIN"
    SYSTEM_SERVICE = "SYSTEM_SERVICE"


class UserContext(BaseModel):
    user_id: str
    email: str
    roles: List[str]
    org_unit_id: Optional[str] = None
    is_service: bool = False

    def has_role(self, role: str) -> bool:
        return role in self.roles or RoleEnum.ADMIN.value in self.roles or self.is_service

    def has_any_role(self, roles: List[str]) -> bool:
        if RoleEnum.ADMIN.value in self.roles or self.is_service:
            return True
        return any(r in self.roles for r in roles)


security_bearer = HTTPBearer(
    auto_error=False,
    description="JWT Bearer Token obtained from POST /api/v1/auth/generate-token (e.g. 'Bearer eyJhbGci...')"
)


def create_access_token(
    user_id: str,
    email: str,
    roles: List[str],
    org_unit_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generates a signed JWT access token for user authentication."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "org_unit_id": org_unit_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "ps02-crm-auth-service"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_service_token(
    service_name: str,
    roles: Optional[List[str]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generates an internal signed service token for inter-service RPC."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=60))
    payload = {
        "sub": service_name,
        "roles": roles or [RoleEnum.SYSTEM_SERVICE.value],
        "is_service": True,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "ps02-service-mesh"
    }
    return jwt.encode(payload, settings.INTERNAL_SERVICE_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> UserContext:
    """Decodes and validates a JWT token against user or service secret."""
    # First try user secret
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return UserContext(
            user_id=payload.get("sub", ""),
            email=payload.get("email", ""),
            roles=payload.get("roles", []),
            org_unit_id=payload.get("org_unit_id"),
            is_service=False
        )
    except jwt.PyJWTError:
        pass

    # Next try service secret
    try:
        payload = jwt.decode(token, settings.INTERNAL_SERVICE_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return UserContext(
            user_id=payload.get("sub", ""),
            email=f"{payload.get('sub')}@internal.service",
            roles=payload.get("roles", [RoleEnum.SYSTEM_SERVICE.value]),
            is_service=True
        )
    except jwt.PyJWTError:
        raise AuthenticationError("Invalid, expired, or malformed authentication token")


async def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    service_token_header: Optional[str] = Header(
        None,
        alias="X-Service-Token",
        title="Internal Service Secret / HMAC Token",
        description="Optional internal microservice authentication token (e.g. ps02-internal-service-hmac-token-2026). Leave blank if authenticating with Bearer JWT token in Authorization header.",
        examples=["ps02-internal-service-hmac-token-2026"]
    )
) -> UserContext:
    """Dependency to extract and validate authenticated user or service."""
    # 1. Check direct service token header
    if service_token_header:
        if service_token_header == settings.INTERNAL_SERVICE_SECRET:
            return UserContext(
                user_id="internal-system",
                email="system@internal.service",
                roles=[RoleEnum.SYSTEM_SERVICE.value, RoleEnum.ADMIN.value],
                is_service=True
            )
        try:
            return verify_token(service_token_header)
        except Exception:
            raise AuthenticationError("Invalid service token")

    # 2. Check Bearer token
    if auth and auth.credentials:
        # Check if direct shared secret was passed as bearer
        if auth.credentials == settings.INTERNAL_SERVICE_SECRET:
            return UserContext(
                user_id="internal-system",
                email="system@internal.service",
                roles=[RoleEnum.SYSTEM_SERVICE.value, RoleEnum.ADMIN.value],
                is_service=True
            )
        return verify_token(auth.credentials)

    # In development/test mode without auth header, if configured, can return default dev user
    if settings.ENVIRONMENT == "test":
        return UserContext(
            user_id="test-admin-user",
            email="test-admin@matkayena.internal",
            roles=[RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.RM.value],
            is_service=False
        )

    raise AuthenticationError("Authentication required: missing Bearer or Service token")


def require_roles(allowed_roles: List[str]):
    """Enforces server-side RBAC access control."""
    def role_checker(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_any_role(allowed_roles):
            raise AuthorizationError(
                f"Access denied: Required one of {allowed_roles}, your roles: {user.roles}"
            )
        return user
    return role_checker


def require_service_auth(
    user: UserContext = Depends(get_current_user)
) -> UserContext:
    """Enforces that only internal services or administrators can call internal APIs."""
    if not (user.is_service or RoleEnum.ADMIN.value in user.roles or RoleEnum.SYSTEM_SERVICE.value in user.roles):
        raise AuthorizationError("Only internal system services or admins are authorized for this operation")
    return user
