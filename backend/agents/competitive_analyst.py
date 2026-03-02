"""
agents/competitive_analyst.py — Agent 4: Competitive Analyst.

Identifies competitors, assesses differentiation, moat, and entry barriers.
"""
from models.schemas import IdeaSchema, CompetitiveAnalysis, SearchSnippet
from services.llm import call_llm_structured

_PROMPT_TEMPLATE = """\
You are a competitive intelligence analyst. Evaluate the competitive landscape
for the business idea below using the provided search evidence.

Business Context:
- Problem: {core_problem}
- Target customer: {target_customer}
- Industry: {industry}
- Revenue model: {revenue_model}

Search Evidence:
{snippets}

Provide:
- top_competitors: list of up to 6 objects with "name" and "notable_strength"
- differentiation_strength: 1–10 (how distinct is this idea vs competitors)
- entry_barrier_score: 1–10 (how hard is it for new entrants — higher = harder = better for incumbent)
- red_flags: up to 5 specific competitive risks
- moat_score: 1–10 (defensibility of the business long-term)

Base your answer strictly on the evidence. If a competitor is not mentioned in
the evidence, only include it if it is universally well-known.
"""


def _format_snippets(snippets: list[SearchSnippet]) -> str:
    lines = [
        f"• {s.title} — {s.snippet[:200]}"
        for s in snippets[:8]
    ]
    return "\n".join(lines) or "No search evidence available."


async def analyse_competition(
    schema: IdeaSchema,
    snippets: list[SearchSnippet],
) -> CompetitiveAnalysis:
    prompt = _PROMPT_TEMPLATE.format(
        core_problem=schema.core_problem,
        target_customer=schema.target_customer,
        industry=schema.industry,
        revenue_model=schema.revenue_model_guess,
        snippets=_format_snippets(snippets),
    )
    return await call_llm_structured(prompt, CompetitiveAnalysis)