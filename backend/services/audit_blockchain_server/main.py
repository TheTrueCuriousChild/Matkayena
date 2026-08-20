"""Server 4 — Audit and Blockchain Server Main Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.audit_blockchain_server.routes.audit import router as audit_router
from backend.services.audit_blockchain_server.routes.health import router as health_router
from backend.services.shared.database import init_db
from backend.services.shared.errors import register_exception_handlers
from backend.services.shared.logging import RequestLoggingMiddleware, setup_logger

logger = setup_logger("audit_blockchain_server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Server 4: Audit & Blockchain Server...")
    init_db()
    yield
    logger.info("Shutting down Server 4: Audit & Blockchain Server...")


app = FastAPI(
    title="PS-02 Server 4: Audit & Blockchain Server",
    description="Tamper-evident audit hashing, cryptographic hash-chain ledger, and blockchain anchoring with failure isolation.",
    version="1.0.0",
    lifespan=lifespan
)

# Exception handlers
register_exception_handlers(app)

# Middlewares
app.add_middleware(RequestLoggingMiddleware, service_name="audit_blockchain_server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router)
app.include_router(audit_router)

if __name__ == "__main__":
    import uvicorn
    from backend.services.shared.config import settings
    uvicorn.run(app, host="0.0.0.0", port=settings.AUDIT_BLOCKCHAIN_SERVER_PORT)
