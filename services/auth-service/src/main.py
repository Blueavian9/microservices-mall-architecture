"""auth-service — FastAPI (PRD Phase 2)."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest, REGISTRY
from starlette.responses import Response

from src import db
from src.events import connect_nats, drain_nats
from src.routers import auth as auth_router
from src.settings import get_settings

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_started = time.monotonic()

_http_requests = Counter(
    "http_requests_total",
    "HTTP requests",
    ["method", "status"],
    registry=REGISTRY,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    if not s.skip_db:
        await db.init_pool()
        assert db.pool is not None
        async with db.pool.acquire() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database ping OK")
        await db.migrate()
        await connect_nats()
    else:
        logger.warning("SKIP_DB=1 — database and NATS disabled (tests/dev only)")
    yield
    if not s.skip_db:
        await drain_nats()
        await db.close_pool()


app = FastAPI(title="auth-service", lifespan=lifespan)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.middleware("http")
async def count_http_requests(request: Request, call_next):
    method = request.method
    response = await call_next(request)
    status = str(response.status_code)
    try:
        _http_requests.labels(method=method, status=status).inc()
    except Exception:
        pass
    return response


def _setup_cors(application: FastAPI) -> None:
    s = get_settings()
    origins = s.cors_origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


_setup_cors(app)


@app.get("/health")
async def root_health():
    return {
        "status": "ok",
        "service": "auth-service",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "uptime": time.monotonic() - _started,
    }


def metrics_payload() -> Response:
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/metrics")
async def metrics_root():
    return metrics_payload()


app.include_router(auth_router.router, prefix="/auth")
app.include_router(auth_router.router, prefix="/api/auth")


@app.get("/auth/metrics", include_in_schema=False)
async def metrics_auth_alias():
    return metrics_payload()
