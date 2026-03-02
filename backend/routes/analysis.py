"""
routes/analysis.py — FastAPI router for analysis endpoints.

Endpoints:
  POST /api/v1/track            — log page view for a device
  POST /api/v1/analyze          — submit idea, kick off background pipeline
  GET  /api/v1/analysis/{id}    — poll for result
  GET  /api/v1/health           — liveness + model status check
"""
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models.database import Analysis, DeviceUsage, Idea, UsageEvent
from models.schemas import (
    AnalyzeRequest, AnalyzeResponse, AnalysisResult,
    AnalysisStatus, HealthResponse, TrackRequest, TrackResponse,
)
from services.database import get_db
from services.embedding import embed, cosine_similarity, get_model
from utils.pipeline import run_analysis

log = structlog.get_logger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1", tags=["analysis"])

DEVICE_HEADER_NAME = "X-Device-Id"
ANALYSIS_DEVICE_LIMIT = 2
DEVICE_LIMIT_MESSAGE = (
    "Device limit reached (2 analyses). Please try again later "
    "or run your own deployment for higher limits."
)


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp for usage events and counters."""
    return datetime.now(timezone.utc)


def _require_device_id(request: Request) -> str:
    """Read and validate the device identifier header."""
    device_id = request.headers.get(DEVICE_HEADER_NAME, "").strip()
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {DEVICE_HEADER_NAME} header.",
        )
    return device_id


async def _get_or_create_device_usage_for_update(
    device_id: str,
    db: AsyncSession,
) -> DeviceUsage:
    """Insert device row if missing, then lock it for a safe counter update."""
    await db.execute(
        insert(DeviceUsage)
        .values(device_id=device_id, last_seen=_utcnow())
        .on_conflict_do_nothing(index_elements=[DeviceUsage.device_id])
    )

    result = await db.execute(
        select(DeviceUsage)
        .where(DeviceUsage.device_id == device_id)
        .with_for_update()
    )
    return result.scalar_one()


# ── Background task wrapper ───────────────────────────────────────────────────

async def _execute_pipeline(
    idea_text: str,
    analysis_id: uuid.UUID,
    tier: str,
    db_session,  # fresh session from context — BackgroundTasks needs its own
) -> None:
    """Runs the full pipeline and persists result to DB."""
    from services.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await run_analysis(idea_text, analysis_id, tier, db)

        await db.execute(
            update(Analysis)
            .where(Analysis.id == analysis_id)
            .values(
                status=result.status.value,
                result_json=result.model_dump(mode="json"),
                completed_at=result.completed_at,
                error=result.error,
            )
        )
        await db.commit()


# ── POST /api/v1/track ────────────────────────────────────────────────────────

@router.post("/track", response_model=TrackResponse)
async def track_page_view(
    body: TrackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TrackResponse:
    """Track a page view for the current device."""
    device_id = _require_device_id(request)

    async with db.begin():
        device_usage = await _get_or_create_device_usage_for_update(device_id, db)
        device_usage.last_seen = _utcnow()
        device_usage.visit_count += 1
        db.add(UsageEvent(device_id=device_id, event_type=body.event_type))

    log.info("route.track", device_id=device_id, event_type=body.event_type)
    return TrackResponse(status="ok")


# ── POST /api/v1/analyze ──────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(
    body: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    """
    Accept an idea, check for near-duplicate cached analyses, then kick off
    the multi-agent pipeline in the background.
    """
    device_id = _require_device_id(request)
    blocked = False

    async with db.begin():
        device_usage = await _get_or_create_device_usage_for_update(device_id, db)
        device_usage.last_seen = _utcnow()

        if device_usage.analysis_count >= ANALYSIS_DEVICE_LIMIT:
            blocked = True
            db.add(
                UsageEvent(
                    device_id=device_id,
                    event_type="analysis_blocked",
                    idea_chars=len(body.idea),
                )
            )
        else:
            device_usage.analysis_count += 1
            db.add(
                UsageEvent(
                    device_id=device_id,
                    event_type="analysis_submit",
                    idea_chars=len(body.idea),
                )
            )

    if blocked:
        log.info("route.analysis_blocked", device_id=device_id)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=DEVICE_LIMIT_MESSAGE)

    idea_embedding = embed(body.idea)

    # ── Deduplication: skip full analysis if similar idea was recently run ────
    recent_ideas = (await db.execute(
        select(Idea).where(Idea.embedding.is_not(None)).order_by(Idea.created_at.desc()).limit(50)
    )).scalars().all()

    for existing in recent_ideas:
        if existing.embedding and cosine_similarity(idea_embedding, existing.embedding) >= settings.cache_similarity_threshold:
            # Return the most recent analysis for this idea
            cached_analysis = (await db.execute(
                select(Analysis)
                .where(Analysis.idea_id == existing.id, Analysis.status == "complete")
                .order_by(Analysis.created_at.desc())
                .limit(1)
            )).scalar_one_or_none()

            if cached_analysis:
                log.info("route.dedup_hit", existing_analysis=str(cached_analysis.id))
                return AnalyzeResponse(
                    analysis_id=str(cached_analysis.id),
                    status=AnalysisStatus.COMPLETE,
                    message="Returning cached analysis for a similar idea.",
                )

    # ── Persist new idea + analysis record ───────────────────────────────────
    idea_record = Idea(raw_text=body.idea, embedding=idea_embedding)
    db.add(idea_record)
    await db.flush()  # get the generated ID

    analysis_record = Analysis(idea_id=idea_record.id, status="pending", tier=body.tier)
    db.add(analysis_record)
    await db.commit()

    # ── Schedule pipeline ─────────────────────────────────────────────────────
    background_tasks.add_task(
        _execute_pipeline, body.idea, analysis_record.id, body.tier, db
    )

    log.info("route.analysis_queued", analysis_id=str(analysis_record.id))
    return AnalyzeResponse(
        analysis_id=str(analysis_record.id),
        status=AnalysisStatus.PENDING,
        message="Analysis queued. Poll /api/v1/analysis/{id} for results (ETA: 20–40s).",
    )


# ── GET /api/v1/analysis/{id} ─────────────────────────────────────────────────

@router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResult:
    """Poll for analysis result. Returns status PENDING/RUNNING until complete."""
    record = (await db.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )).scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    if record.result_json:
        return AnalysisResult.model_validate(record.result_json)

    # Not yet complete — return minimal status response
    return AnalysisResult(
        id=analysis_id,
        idea_text="",
        status=AnalysisStatus(record.status),
    )


# ── GET /api/v1/health ────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness check used by Render and monitoring tools."""
    try:
        model_loaded = get_model() is not None
    except RuntimeError:
        model_loaded = False

    return HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        env=settings.app_env,
    )
