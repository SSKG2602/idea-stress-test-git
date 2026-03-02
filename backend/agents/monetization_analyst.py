"""
agents/monetization_analyst.py — Agent 5: Monetization Analyst.

Evaluates willingness to pay, CAC risk, LTV feasibility, and monetisation difficulty.
"""
from models.schemas import IdeaSchema, MonetizationAnalysis, SearchSnippet
from services.llm import call_llm_structured

_PROMPT_TEMPLATE = """\
You are a monetisation and unit-economics analyst. Assess the revenue potential
of the business idea below.

Business Context:
- Problem: {core_problem}
- Target customer: {target_customer}
- Revenue model: {revenue_model}
- Assumed price point: {price_point}
- Industry: {industry}

Search Evidence:
{snippets}

Evaluate:
- willingness_to_pay_score: 1–10 (how likely are customers to pay; 10=very likely)
- cac_risk_score: 1–10 (risk that customer acquisition costs are unsustainably high; 10=very high risk)
- ltv_feasibility: 1–10 (likelihood of achieving positive LTV; 10=very feasible)
- monetization_difficulty: 1–10 (overall difficulty of making money; 10=very hard)

Ground your scores in the search evidence where possible. If evidence is sparse,
reflect uncertainty with mid-range scores (4–6) rather than extreme values.
"""


def _format_snippets(snippets: list[SearchSnippet]) -> str:
    return "\n".join(
        f"• {s.title} — {s.snippet[:200]}"
        for s in snippets[:8]
    ) or "No search evidence available."


async def analyse_monetization(
    schema: IdeaSchema,
    snippets: list[SearchSnippet],
) -> MonetizationAnalysis:
    prompt = _PROMPT_TEMPLATE.format(
        core_problem=schema.core_problem,
        target_customer=schema.target_customer,
        revenue_model=schema.revenue_model_guess,
        price_point=schema.assumed_price_point,
        industry=schema.industry,
        snippets=_format_snippets(snippets),
    )
    return await call_llm_structured(prompt, MonetizationAnalysis)