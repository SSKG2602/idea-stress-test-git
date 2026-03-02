"""
utils/pipeline.py — Analysis pipeline orchestrator.

Sequence:
  Agent 1  → extract structured schema from idea text
  Agent 2  → generate 6 targeted search queries
  Search   → multi-query Serper search with 24h cache
  FAISS    → index all snippets for semantic retrieval
  Agent 3  → market analysis (uses top relevant snippets)
  Agent 4  → competitive analysis
  Agent 5  → monetisation analysis
  Agent 6  → failure simulation (paid tier only)
  Agent 7  → audit pass over all outputs
  Scoring  → compute weighted viability score

Concurrency is limited to MAX_CONCURRENT_ANALYSES (2) via asyncio.Semaphore
to keep Render free-tier RAM stable.
"""
import asyncio
import uuid
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from agents import (
    extract_schema, generate_queries, analyse_market,
    analyse_competition, analyse_monetization,
    simulate_failure, audit_analysis,
)
from config import get_settings
from models.schemas import AnalysisResult, AnalysisStatus
from services.embedding import EphemeralIndex
from services.search import multi_search
from utils.scoring import calculate_viability

log = structlog.get_logger(__name__)
settings = get_settings()

# Global semaphore — shared across all requests in the process
_semaphore = asyncio.Semaphore(settings.max_concurrent_analyses)


async def run_analysis(
    idea_text: str,
    analysis_id: uuid.UUID,
    tier: str,
    db: AsyncSession,
) -> AnalysisResult:
    """
    Execute the full multi-agent pipeline for a given idea.
    Blocks if MAX_CONCURRENT_ANALYSES slots are occupied.
    """
    async with _semaphore:
        log.info("pipeline.start", analysis_id=str(analysis_id), tier=tier)
        result = AnalysisResult(id=analysis_id, idea_text=idea_text, status=AnalysisStatus.RUNNING)

        try:
            # ── Step 1: Normalise idea ────────────────────────────────────────
            log.info("pipeline.agent1_schema")
            result.idea_schema = await extract_schema(idea_text)

            # ── Step 2: Generate search queries ───────────────────────────────
            log.info("pipeline.agent2_queries")
            queries = await generate_queries(result.idea_schema)

            # ── Step 3: Execute searches and build FAISS index ────────────────
            log.info("pipeline.search", query_count=len(queries))
            snippets = await multi_search(queries, db)
            result.search_snippets_used = len(snippets)

            index = EphemeralIndex()
            if snippets:
                index.add([f"{s.title} {s.snippet}" for s in snippets])

            # ── Step 4–6: Parallel analyst agents ────────────────────────────
            # Market, competitive, and monetisation analyses are independent —
            # run them concurrently to cut wall-clock time.
            log.info("pipeline.agents_3_4_5_parallel")
            market_snippets      = snippets  # all agents see all snippets
            competitive_snippets = snippets
            monetization_snippets= snippets

            market_task      = analyse_market(result.idea_schema, market_snippets)
            competitive_task = analyse_competition(result.idea_schema, competitive_snippets)
            monetization_task= analyse_monetization(result.idea_schema, monetization_snippets)

            (
                result.market,
                result.competitive,
                result.monetization,
            ) = await asyncio.gather(market_task, competitive_task, monetization_task)

            # ── Step 7: Failure simulation (paid only) ────────────────────────
            if tier == "paid":
                log.info("pipeline.agent6_failure")
                result.failure = await simulate_failure(
                    result.idea_schema, result.market,
                    result.competitive, result.monetization,
                )

            # ── Step 8: Audit ─────────────────────────────────────────────────
            log.info("pipeline.agent7_audit")
            result.audit = await audit_analysis(
                result.idea_schema, result.market,
                result.competitive, result.monetization,
                result.failure,
            )

            # ── Step 9: Score ─────────────────────────────────────────────────
            result.viability = calculate_viability(
                result.market, result.competitive,
                result.monetization, result.failure,
            )

            result.status = AnalysisStatus.COMPLETE
            result.completed_at = datetime.utcnow()
            log.info("pipeline.complete", score=result.viability.scaled_score)

        except Exception as exc:
            log.error("pipeline.failed", error=str(exc))
            result.status = AnalysisStatus.FAILED
            result.error = str(exc)

        return result
