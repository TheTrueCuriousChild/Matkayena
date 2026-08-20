"""Standard error types and exception handling for all services."""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class BadRequestError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            details=details,
        )


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication required or invalid credentials"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHENTICATED",
        )


class AuthorizationError(AppException):
    def __init__(self, message: str = "Access denied: insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="UNAUTHORIZED",
        )


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class ConflictError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details,
        )


class IdempotencyConflictError(AppException):
    def __init__(self, idempotency_key: str, existing_result: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Duplicate request detected for idempotency key '{idempotency_key}'",
            status_code=status.HTTP_409_CONFLICT,
            error_code="IDEMPOTENCY_CONFLICT",
            details={"idempotency_key": idempotency_key, "existing_result": existing_result},
        )


class ValidationError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class ServiceUnavailableError(AppException):
    def __init__(self, service_name: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Upstream service '{service_name}' is currently unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details={"service_name": service_name},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform exception handlers on a FastAPI application."""
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
                correlation_id=correlation_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred.",
                details={"error_type": exc.__class__.__name__},
                correlation_id=correlation_id,
            ).model_dump(),
        )
