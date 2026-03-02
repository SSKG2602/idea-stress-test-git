"""
agents/query_generator.py — Agent 2: Search Query Generator.

Produces exactly 6 search queries covering all required research dimensions.
Each query targets a distinct signal so search results don't overlap.
"""
from models.schemas import IdeaSchema, SearchQueries
from services.llm import call_llm_structured

_DIMENSIONS = [
    "total addressable market size and revenue",
    "direct competitors and market leaders",
    "industry growth trends and forecasts",
    "startup funding and investor activity",
    "industry risks and failure cases",
    "regulatory landscape and compliance requirements",
]

_PROMPT_TEMPLATE = """\
You are a market research query specialist.

Generate exactly 6 search queries to research the business idea described below.
Each query must target a DIFFERENT research dimension (listed below) and be optimised
for a web search engine (concise, keyword-rich, no question marks).

Research dimensions (one query per dimension, in order):
{dimensions}

Business idea context:
- Problem: {core_problem}
- Industry: {industry}
- Geography: {geography}
- Target customer: {target_customer}

Return a JSON object with a single key "queries" containing an array of exactly 6 strings.
"""


async def generate_queries(schema: IdeaSchema) -> list[str]:
    """Return 6 search queries derived from the structured idea schema."""
    dimensions_str = "\n".join(f"{i+1}. {d}" for i, d in enumerate(_DIMENSIONS))
    prompt = _PROMPT_TEMPLATE.format(
        dimensions=dimensions_str,
        core_problem=schema.core_problem,
        industry=schema.industry,
        geography=schema.geography,
        target_customer=schema.target_customer,
    )
    result = await call_llm_structured(prompt, SearchQueries)
    return result.queries