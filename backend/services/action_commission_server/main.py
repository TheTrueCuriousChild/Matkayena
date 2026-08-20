"""Server 3 — Action and Commission Server Main Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.action_commission_server.routes.actions import router as actions_router
from backend.services.action_commission_server.routes.health import router as health_router
from backend.services.shared.database import init_db
from backend.services.shared.errors import register_exception_handlers
from backend.services.shared.logging import RequestLoggingMiddleware, setup_logger

logger = setup_logger("action_commission_server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Server 3: Action & Commission Server...")
    init_db()
    yield
    logger.info("Shutting down Server 3: Action & Commission Server...")


app = FastAPI(
    title="PS-02 Server 3: Action & Commission Server",
    description="RM task execution, lifecycle state machine, outcome recording, and deterministic commission engine.",
    version="1.0.0",
    lifespan=lifespan
)

# Exception handlers
register_exception_handlers(app)

# Middlewares
app.add_middleware(RequestLoggingMiddleware, service_name="action_commission_server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router)
app.include_router(actions_router)

if __name__ == "__main__":
    import uvicorn
    from backend.services.shared.config import settings
    uvicorn.run(app, host="0.0.0.0", port=settings.ACTION_COMMISSION_SERVER_PORT)
