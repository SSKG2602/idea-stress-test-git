"""
agents/failure_simulator.py — Agent 6: Failure Simulator (paid tier).

Adversarially stress-tests the idea by enumerating failure modes and
estimating survival probabilities under three hostile scenarios.
"""
from models.schemas import (
    IdeaSchema, MarketAnalysis, CompetitiveAnalysis,
    MonetizationAnalysis, FailureSimulation
)
from services.llm import call_llm_structured

_PROMPT_TEMPLATE = """\
You are a venture capital red-team analyst. Your job is to stress-test this
business idea by finding every realistic way it could fail.

Business Idea:
- Problem: {core_problem}
- Industry: {industry}
- Revenue model: {revenue_model}
- Target customer: {target_customer}

Prior Analysis Summary:
- Market saturation score: {saturation}/10
- Differentiation strength: {differentiation}/10
- Moat score: {moat}/10
- Monetisation difficulty: {mon_difficulty}/10
- CAC risk: {cac_risk}/10

Task:
1. List exactly 7 distinct, specific failure modes (not generic platitudes).
   Each should be 1–2 sentences describing a concrete failure path.
2. Identify the single highest-risk area (one phrase).
3. Estimate survival probabilities (0–100) under each hostile scenario:
   - Economic downturn (customers cut budgets, VC funding dries up)
   - Regulatory crackdown (new laws or compliance requirements)
   - Well-funded competitor enters the exact same market

Be brutally realistic. Do not soften the analysis.
"""


async def simulate_failure(
    schema: IdeaSchema,
    market: MarketAnalysis,
    competitive: CompetitiveAnalysis,
    monetization: MonetizationAnalysis,
) -> FailureSimulation:
    prompt = _PROMPT_TEMPLATE.format(
        core_problem=schema.core_problem,
        industry=schema.industry,
        revenue_model=schema.revenue_model_guess,
        target_customer=schema.target_customer,
        saturation=market.saturation_score,
        differentiation=competitive.differentiation_strength,
        moat=competitive.moat_score,
        mon_difficulty=monetization.monetization_difficulty,
        cac_risk=monetization.cac_risk_score,
    )
    return await call_llm_structured(prompt, FailureSimulation)