from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.middleware.rate_limiter import limiter
from app.routers import (
    auth,
    users,
    resources,
    bookings,
    conditions,
    contracts,
    incidents,
    chat,
    notifications,
    admin,
    websocket,
)


from app.database import Base, engine, is_sqlite
import app.models  # ensure models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    if is_sqlite:
        for table in Base.metadata.tables.values():
            for column in table.columns:
                if column.server_default is not None:
                    arg_str = str(getattr(column.server_default, "arg", ""))
                    if "gen_random_uuid" in arg_str:
                        column.server_default = None
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown tasks


app = FastAPI(
    title="Availo API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# SlowAPI state & rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with /api/v1 prefix
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(resources.router, prefix="/api/v1/resources", tags=["resources"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
app.include_router(conditions.router, prefix="/api/v1/conditions", tags=["conditions"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["contracts"])
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

# WebSocket router mounted at root /ws
app.include_router(websocket.router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Availo"}
