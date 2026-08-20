"""Server 2 — Event and Intelligence Server Main Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.event_intelligence_server.routes.events import router as events_router
from backend.services.event_intelligence_server.routes.health import router as health_router
from backend.services.event_intelligence_server.routes.intelligence import router as intelligence_router
from backend.services.shared.database import init_db
from backend.services.shared.errors import register_exception_handlers
from backend.services.shared.logging import RequestLoggingMiddleware, setup_logger

logger = setup_logger("event_intelligence_server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Server 2: Event & Intelligence Server...")
    init_db()
    yield
    logger.info("Shutting down Server 2: Event & Intelligence Server...")


app = FastAPI(
    title="PS-02 Server 2: Event & Intelligence Server",
    description="Event ingestion, validation, idempotency, routing, and 3 autonomous deterministic agents (Opportunity, Performance, Manager).",
    version="1.0.0",
    lifespan=lifespan
)

# Exception handlers
register_exception_handlers(app)

# Middlewares
app.add_middleware(RequestLoggingMiddleware, service_name="event_intelligence_server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router)
app.include_router(events_router)
app.include_router(intelligence_router)

if __name__ == "__main__":
    import uvicorn
    from backend.services.shared.config import settings
    uvicorn.run(app, host="0.0.0.0", port=settings.EVENT_INTELLIGENCE_SERVER_PORT)
