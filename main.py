from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import get_db, engine
from models.user import Base
from routes.auth import router as auth_router
from routes.lane import router as lane_router
from routes.admin import router as admin_router
from routes.analytics import router as analytics_router

# ── Rate limiter ──────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="4viso Backend", lifespan=lifespan)

# ── Rate limit handler ────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────
# Origins come from the ALLOWED_ORIGINS env var (comma-separated).
# Falls back to the local dev frontend if unset.
import os

_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global error handlers ─────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = []
    for e in exc.errors():
        errors.append({
            "field":   " → ".join(str(x) for x in e["loc"]),
            "message": e["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={"error": "Validation failed", "details": errors}
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"error": "Database error", "detail": str(exc)}
    )

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# ── Health check ──────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Backend is running!"}

@app.get("/spy-data")
async def check_db(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT version();"))
        version = result.scalar()
        return {"status": "PostgreSQL is connected!", "version": version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ── Routers ───────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(lane_router)
app.include_router(admin_router)
app.include_router(analytics_router)