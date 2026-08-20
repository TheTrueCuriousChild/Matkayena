"""Resilient asynchronous HTTP client for internal microservice communication."""

import asyncio
from typing import Any, Dict, Optional
import httpx
from backend.services.shared.config import settings
from backend.services.shared.errors import ServiceUnavailableError, AppException


class ServiceClient:
    def __init__(self, service_name: str, base_url: str, timeout: Optional[float] = None, max_retries: Optional[int] = None):
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        if settings.ENVIRONMENT == "test":
            self.timeout = timeout or 0.2
            self.max_retries = max_retries or 1
        else:
            self.timeout = timeout or 10.0
            self.max_retries = max_retries or 3


    def _build_headers(
        self,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        source_service: Optional[str] = None
    ) -> Dict[str, str]:
        import uuid
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Request-ID": request_id or str(uuid.uuid4()),
            "X-Correlation-ID": correlation_id or str(uuid.uuid4()),
            "X-Source-Service": source_service or "internal_client",
            "X-Service-Token": settings.INTERNAL_SERVICE_SECRET,
        }

    async def post(
        self,
        endpoint: str,
        json_data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        source_service: Optional[str] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._build_headers(correlation_id, request_id, source_service)
        timeout = 0.15 if settings.ENVIRONMENT == "test" else self.timeout
        retries = 1 if settings.ENVIRONMENT == "test" else self.max_retries

        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=json_data, headers=headers)
                    if response.status_code >= 500:
                        raise httpx.HTTPStatusError(
                            f"Server returned {response.status_code}",
                            request=response.request,
                            response=response
                        )
                    if response.status_code >= 400:
                        data = response.json() if response.content else {}
                        raise AppException(
                            message=data.get("message", f"Request failed with status {response.status_code}"),
                            status_code=response.status_code,
                            error_code=data.get("error_code", "UPSTREAM_ERROR"),
                            details=data.get("details", {})
                        )
                    return response.json() if response.content else {}
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
            except AppException:
                raise
            except Exception as e:
                last_exception = e
                break

        raise ServiceUnavailableError(
            service_name=self.service_name,
            message=f"Failed to communicate with {self.service_name} at {url} after {self.max_retries} attempts: {last_exception}"
        )

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        source_service: Optional[str] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._build_headers(correlation_id, request_id, source_service)
        timeout = 0.15 if settings.ENVIRONMENT == "test" else self.timeout
        retries = 1 if settings.ENVIRONMENT == "test" else self.max_retries

        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
                    if response.status_code >= 500:
                        raise httpx.HTTPStatusError(
                            f"Server returned {response.status_code}",
                            request=response.request,
                            response=response
                        )
                    if response.status_code >= 400:
                        data = response.json() if response.content else {}
                        raise AppException(
                            message=data.get("message", f"Request failed with status {response.status_code}"),
                            status_code=response.status_code,
                            error_code=data.get("error_code", "UPSTREAM_ERROR"),
                            details=data.get("details", {})
                        )
                    return response.json() if response.content else {}
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
            except AppException:
                raise
            except Exception as e:
                last_exception = e
                break

        raise ServiceUnavailableError(
            service_name=self.service_name,
            message=f"Failed to communicate with {self.service_name} at {url} after {self.max_retries} attempts: {last_exception}"
        )
