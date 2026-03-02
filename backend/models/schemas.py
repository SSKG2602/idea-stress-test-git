"""
models/schemas.py — Pydantic schemas for every agent output and API contract.
All LLM responses are validated against these before being used downstream.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


# ── Agent 1: Schema Extractor ─────────────────────────────────────────────────

class IdeaSchema(BaseModel):
    """Structured representation extracted from raw idea text."""
    core_problem: str = Field(..., description="The problem being solved")
    target_customer: str
    industry: str
    geography: str
    revenue_model_guess: str
    assumed_price_point: str
    complexity_level: int = Field(..., ge=1, le=5)


# ── Agent 2: Search Query Generator ──────────────────────────────────────────

class SearchQueries(BaseModel):
    """Six focused queries covering all research dimensions."""
    queries: list[str] = Field(..., min_length=6, max_length=6)


# ── Agent 3: Market Analyst ───────────────────────────────────────────────────

class MarketAnalysis(BaseModel):
    tam_estimate_range: str = Field(..., description="e.g. '$2B–$8B'")
    market_growth_rate: str = Field(..., description="e.g. '14% CAGR'")
    saturation_score: int = Field(..., ge=1, le=10)   # 10 = fully saturated
    trend_direction: TrendDirection
    confidence: float = Field(..., ge=0.0, le=1.0)


# ── Agent 4: Competitive Analyst ──────────────────────────────────────────────

class Competitor(BaseModel):
    name: str
    notable_strength: str

class CompetitiveAnalysis(BaseModel):
    top_competitors: list[Competitor] = Field(..., max_length=6)
    differentiation_strength: int = Field(..., ge=1, le=10)
    entry_barrier_score: int = Field(..., ge=1, le=10)
    red_flags: list[str] = Field(..., max_length=5)
    moat_score: int = Field(..., ge=1, le=10)


# ── Agent 5: Monetization Analyst ────────────────────────────────────────────

class MonetizationAnalysis(BaseModel):
    willingness_to_pay_score: int = Field(..., ge=1, le=10)
    cac_risk_score: int = Field(..., ge=1, le=10)       # 10 = very high CAC risk
    ltv_feasibility: int = Field(..., ge=1, le=10)
    monetization_difficulty: int = Field(..., ge=1, le=10)


# ── Agent 6: Failure Simulator ────────────────────────────────────────────────

class FailureSimulation(BaseModel):
    top_7_failure_modes: list[str] = Field(..., min_length=7, max_length=7)
    highest_risk_area: str
    survival_probability_downturn: int = Field(..., ge=0, le=100)
    survival_probability_regulation: int = Field(..., ge=0, le=100)
    survival_probability_competition: int = Field(..., ge=0, le=100)


# ── Agent 7: Auditor ──────────────────────────────────────────────────────────

class AuditResult(BaseModel):
    unsupported_claims: list[str]
    uncertainty_flags: list[str]
    overall_confidence_score: int = Field(..., ge=0, le=100)


# ── Scoring Engine Output ─────────────────────────────────────────────────────

class ViabilityScore(BaseModel):
    """Weighted composite score 0–100."""
    raw_score: float
    scaled_score: int                     # 0–100, what users see
    breakdown: dict[str, float]           # component → contribution


# ── Search layer ──────────────────────────────────────────────────────────────

class SearchSnippet(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: str | None = None     # ISO date string from Serper
    is_fresh: bool = True                 # set False if older than threshold


# ── Full Analysis Result ──────────────────────────────────────────────────────

class AnalysisResult(BaseModel):
    id: uuid.UUID
    idea_text: str
    status: AnalysisStatus
    idea_schema: IdeaSchema | None = None
    market: MarketAnalysis | None = None
    competitive: CompetitiveAnalysis | None = None
    monetization: MonetizationAnalysis | None = None
    failure: FailureSimulation | None = None
    audit: AuditResult | None = None
    viability: ViabilityScore | None = None
    search_snippets_used: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    error: str | None = None


# ── API Request / Response ────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    idea: str = Field(..., min_length=20, max_length=2000,
                      description="Your business idea (20–2000 chars)")
    tier: Literal["free", "paid"] = "free"

    @field_validator("idea")
    @classmethod
    def no_empty_idea(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Idea cannot be blank")
        return v.strip()

class AnalyzeResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    message: str

class TrackRequest(BaseModel):
    event_type: Literal["page_view"]

class TrackResponse(BaseModel):
    status: str

class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    status: str
    model_loaded: bool
    env: str
