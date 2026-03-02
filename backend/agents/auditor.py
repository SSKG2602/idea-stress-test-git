"""
agents/auditor.py — Agent 7: Auditor.

Final pass over all agent outputs.
Flags unsupported claims, internal contradictions, and low-confidence areas.
Produces an overall confidence score for the full analysis.
"""
import json
from models.schemas import (
    IdeaSchema, MarketAnalysis, CompetitiveAnalysis,
    MonetizationAnalysis, FailureSimulation, AuditResult
)
from services.llm import call_llm_structured

_PROMPT_TEMPLATE = """\
You are a senior analytical auditor. Review the complete set of agent outputs
for this business idea analysis and identify any weaknesses.

Business Idea Schema:
{schema}

Market Analysis:
{market}

Competitive Analysis:
{competitive}

Monetisation Analysis:
{monetization}

{failure_section}

Your audit must identify:
1. unsupported_claims: specific claims made by agents that lack evidence backing
   (list as strings, max 5; empty list if none)
2. uncertainty_flags: areas where confidence is low or data was thin
   (list as strings, max 5; empty list if none)
3. overall_confidence_score: 0–100 reflecting how much trust to place in this
   complete analysis (100=fully evidenced, 0=entirely speculative)

Be specific. Generic flags like "market data may be inaccurate" are not useful.
"""


def _dump(obj) -> str:
    return json.dumps(obj.model_dump(), indent=2)


async def audit_analysis(
    schema: IdeaSchema,
    market: MarketAnalysis,
    competitive: CompetitiveAnalysis,
    monetization: MonetizationAnalysis,
    failure: FailureSimulation | None = None,
) -> AuditResult:
    failure_section = (
        f"Failure Simulation:\n{_dump(failure)}"
        if failure else
        "Failure Simulation: not run (free tier)"
    )
    prompt = _PROMPT_TEMPLATE.format(
        schema=_dump(schema),
        market=_dump(market),
        competitive=_dump(competitive),
        monetization=_dump(monetization),
        failure_section=failure_section,
    )
    return await call_llm_structured(prompt, AuditResult)