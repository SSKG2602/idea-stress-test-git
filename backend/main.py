"""
main.py — FastAPI application entry point.
Startup sequence:
  1. Load SentenceTransformer model into memory (once).
  2. Register routes + middleware.
  3. Serve via Gunicorn + Uvicorn workers (see Dockerfile / render.yaml).
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import get_settings
from routes.analysis import router
from services.embedding import load_model

log = structlog.get_logger(__name__)
settings = get_settings()

# ── Lifespan: startup / shutdown ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the embedding model before accepting requests."""
    log.info("app.startup", env=settings.app_env)
    load_model(settings.embedding_model)
    yield
    log.info("app.shutdown")

# ── Rate limiter (per-IP) ─────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Idea Stress-Test Engine",
    description="Multi-agent LLM pipeline for rigorous business idea analysis.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)

# ── Local dev entrypoint ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)