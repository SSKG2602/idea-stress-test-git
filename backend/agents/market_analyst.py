"""
agents/market_analyst.py — Agent 3: Market Analyst.

Analyses search snippets to estimate market size, growth, and saturation.
Receives timestamped snippets so it can weight recency appropriately.
"""
from models.schemas import IdeaSchema, MarketAnalysis, SearchSnippet
from services.llm import call_llm_structured

_PROMPT_TEMPLATE = """\
You are a senior market analyst. Analyse the search evidence below to assess the
market opportunity for this business idea.

Business Context:
- Problem: {core_problem}
- Industry: {industry}
- Geography: {geography}

Search Evidence (title | date | snippet):
{snippets}

Based ONLY on the evidence provided:
- Estimate TAM as a range (e.g. "$2B–$8B globally")
- Estimate market growth rate (e.g. "14% CAGR 2024–2028")
- Score market saturation 1–10 (1=wide open, 10=fully saturated)
- Determine trend direction: "up", "down", or "stable"
- Rate your confidence 0.0–1.0 based on evidence quality

If evidence is thin, reflect that in a low confidence score — do not fabricate data.
"""


def _format_snippets(snippets: list[SearchSnippet]) -> str:
    lines = []
    for s in snippets[:8]:  # cap at 8 to control prompt length
        date_str = s.published_date or "unknown date"
        lines.append(f"• [{date_str}] {s.title} — {s.snippet[:200]}")
    return "\n".join(lines) or "No search evidence available."


async def analyse_market(schema: IdeaSchema, snippets: list[SearchSnippet]) -> MarketAnalysis:
    """Return market analysis grounded in the provided search snippets."""
    prompt = _PROMPT_TEMPLATE.format(
        core_problem=schema.core_problem,
        industry=schema.industry,
        geography=schema.geography,
        snippets=_format_snippets(snippets),
    )
    return await call_llm_structured(prompt, MarketAnalysis)