"""Server 1 — Core / API Server Main Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.core_server.routes.actions import router as actions_router
from backend.services.core_server.routes.audit import router as audit_router
from backend.services.core_server.routes.auth import router as auth_router
from backend.services.core_server.routes.customer import router as customer_router
from backend.services.core_server.routes.events import router as events_router
from backend.services.core_server.routes.health import router as health_router
from backend.services.core_server.routes.manager import router as manager_router
from backend.services.core_server.routes.opportunities import router as opportunities_router
from backend.services.core_server.routes.performance import router as performance_router
from backend.services.shared.database import init_db
from backend.services.shared.errors import register_exception_handlers
from backend.services.shared.logging import RequestLoggingMiddleware, setup_logger

logger = setup_logger("core_server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Server 1: Core / API Server...")
    init_db()
    yield
    logger.info("Shutting down Server 1: Core / API Server...")


app = FastAPI(
    title="PS-02 Server 1: Core / API Server",
    description="External API Gateway for PS-02 Event-Driven Sales Intelligence & Actionable CRM.",
    version="1.0.0",
    lifespan=lifespan
)

# Exception handlers
register_exception_handlers(app)

# Middlewares
app.add_middleware(RequestLoggingMiddleware, service_name="core_server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(opportunities_router)
app.include_router(actions_router)
app.include_router(performance_router)
app.include_router(manager_router)
app.include_router(customer_router)
app.include_router(audit_router)

if __name__ == "__main__":
    import uvicorn
    from backend.services.shared.config import settings
    uvicorn.run(app, host="0.0.0.0", port=settings.CORE_SERVER_PORT)
