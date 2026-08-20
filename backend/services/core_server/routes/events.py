"""Event submission gateway endpoint for Server 1."""

from fastapi import APIRouter, Depends, Request, status
from backend.services.shared.auth import get_current_user, UserContext
from backend.services.shared.config import settings
from backend.services.shared.events import EventProcessingResult, EventSubmissionRequest
from backend.services.shared.http_client import ServiceClient

router = APIRouter(prefix="/api/v1/events", tags=["Events Gateway"])
event_client = ServiceClient("event_intelligence_server", settings.EVENT_INTELLIGENCE_SERVER_URL)


@router.post("", response_model=EventProcessingResult, status_code=status.HTTP_200_OK)
async def submit_event(
    req: EventSubmissionRequest,
    request: Request,
    user: UserContext = Depends(get_current_user)
):
    """External entrypoint for commercial, transaction, and CRM events.

    Delegates to Server 2 (Event & Intelligence Server).
    """
    correlation_id = req.correlation_id or getattr(request.state, "correlation_id", None)
    request_id = getattr(request.state, "request_id", None)

    # Ingest through Server 2
    res = await event_client.post(
        endpoint="/api/v1/events/ingest",
        json_data=req.model_dump(mode="json"),
        correlation_id=correlation_id,
        request_id=request_id,
        source_service="core_server"
    )
    return res
