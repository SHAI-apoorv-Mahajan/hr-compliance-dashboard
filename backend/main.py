"""FastAPI entry point.

Startup sequence (PRD §25):
1. Load env via pydantic-settings (config.get_settings, eagerly at import).
2. create_all(engine) — idempotent.
3. seed_defaults — HR user + 8 email templates + 9 flag thresholds (FR-017).
   ONLY config rows. No employee, attendance, or leave data is ever seeded —
   that data enters strictly via Excel uploads → medallion pipeline.

All error responses are {"detail": "..."} per NFR-005.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from database import Base, SessionLocal, engine
from schema_align import widen_columns
from routers import (
    analytics,
    attendance,
    auth,
    email,
    employees,
    flags,
    leave,
    pipeline,
    settings as settings_router,
    upload,
)
from seed import seed_defaults


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)sZ %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("startup: create_all")
    Base.metadata.create_all(engine)
    log.info("startup: schema_align")
    widen_columns(engine)
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()
    log.info("startup: ready")
    yield


_settings = get_settings()

app = FastAPI(title="HR Compliance Dashboard", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# --- Error handlers — guarantee {"detail": "..."} shape (NFR-005) ----------

@app.exception_handler(HTTPException)
async def _http_exc(_req: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def _validation_exc(_req: Request, exc: RequestValidationError) -> JSONResponse:
    # Surface a concise message; do not echo the entire pydantic error tree.
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = ".".join(str(p) for p in first.get("loc", []) if p not in ("body", "query", "path"))
        msg = first.get("msg", "Invalid input")
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "Invalid input"
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(Exception)
async def _unhandled(_req: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# --- Routers --------------------------------------------------------------

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(pipeline.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leave.router)
app.include_router(flags.router)
app.include_router(email.router)
app.include_router(settings_router.router)
app.include_router(analytics.router)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
