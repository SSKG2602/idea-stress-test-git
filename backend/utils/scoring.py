"""
utils/scoring.py — Weighted viability scoring engine.

Formula (from architecture spec):
  Viability =
    (0.25 × (10 - saturation_score))   ← lower saturation = better
    (0.20 × moat_score)                ← defensibility
    (0.20 × (10 - monetization_difficulty)) ← easier to monetise = better
    (0.15 × entry_barrier_score)       ← harder to copy = better
    (0.20 × avg_survival_probability / 10)  ← resilience

Raw result is 0–10, scaled to 0–100 for display.
"""
from models.schemas import (
    MarketAnalysis, CompetitiveAnalysis,
    MonetizationAnalysis, FailureSimulation, ViabilityScore
)


def calculate_viability(
    market: MarketAnalysis,
    competitive: CompetitiveAnalysis,
    monetization: MonetizationAnalysis,
    failure: FailureSimulation | None = None,
) -> ViabilityScore:
    """
    Compute weighted viability score. If failure simulation was not run
    (free tier), the survival component uses a neutral mid-point (50).
    """
    # ── Component calculations ────────────────────────────────────────────────
    market_openness     = 10 - market.saturation_score          # invert saturation
    moat                = competitive.moat_score
    monetization_ease   = 10 - monetization.monetization_difficulty
    barrier             = competitive.entry_barrier_score

    if failure:
        avg_survival = (
            failure.survival_probability_downturn +
            failure.survival_probability_regulation +
            failure.survival_probability_competition
        ) / 3
    else:
        avg_survival = 50.0  # neutral assumption for free tier

    # ── Weighted sum (0–10 scale) ─────────────────────────────────────────────
    raw = (
        0.25 * market_openness +
        0.20 * moat +
        0.20 * monetization_ease +
        0.15 * barrier +
        0.20 * (avg_survival / 10)
    )

    scaled = min(100, max(0, round(raw * 10)))  # 0–100

    breakdown = {
        "market_openness":    round(0.25 * market_openness, 3),
        "moat":               round(0.20 * moat, 3),
        "monetization_ease":  round(0.20 * monetization_ease, 3),
        "entry_barrier":      round(0.15 * barrier, 3),
        "survival_resilience":round(0.20 * (avg_survival / 10), 3),
    }

    return ViabilityScore(raw_score=round(raw, 4), scaled_score=scaled, breakdown=breakdown)