from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import traceback
import os

from app.config import settings
from app.services.scheduler_service import start_scheduler, shutdown_scheduler
from app.routers import (
    auth,
    users,
    resources,
    bookings,
    verification,
    inspections,
    incidents,
    agreements,
    notifications,
    admin
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("availo")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[Availo/ResourcX API] Starting application services...")
    if os.environ.get("TESTING") != "1":
        try:
            await start_scheduler()
        except Exception as e:
            logger.warning(f"Scheduler start skipped or failed: {e}")
    yield
    logger.info("[Availo/ResourcX API] Shutting down application services...")
    if os.environ.get("TESTING") != "1":
        try:
            await shutdown_scheduler()
        except Exception as e:
            logger.warning(f"Scheduler shutdown error: {e}")


app = FastAPI(
    title=settings.APP_NAME if hasattr(settings, "APP_NAME") else "Availo / ResourcX API",
    description="Unified Backend API for Institutional Resource Sharing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Global exception handler returning JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    err_tb = traceback.format_exc()
    logger.error(f"[GlobalException] Unhandled error at {request.method} {request.url}: {exc}\n{err_tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        getattr(settings, "FRONTEND_URL", "http://localhost:3000"),
        getattr(settings, "FRONTEND_ORIGIN", "http://localhost:3000"),
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers both at root (for ResourcX frontend client) and at /api/v1 (for legacy/Availo client)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resources.router)
app.include_router(bookings.router)
app.include_router(verification.router)
app.include_router(inspections.router)
app.include_router(incidents.router)
app.include_router(agreements.router)
app.include_router(notifications.router)
app.include_router(admin.router)

# Mount same routers under /api/v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(resources.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(verification.router, prefix="/api/v1")
app.include_router(inspections.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(agreements.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "Availo / ResourcX",
        "environment": getattr(settings, "ENVIRONMENT", "development"),
    }
