"""
agents/schema_extractor.py — Agent 1: Schema Extractor.

Converts free-form idea text into a structured IdeaSchema.
Runs first in the pipeline; all downstream agents consume its output.
Temperature: 0.2 — prioritise consistency over creativity.
"""
from models.schemas import IdeaSchema
from services.llm import call_llm_structured

_PROMPT_TEMPLATE = """\
Extract a structured business idea schema from the following raw idea text.

Be precise and concise. If a field cannot be determined, make the best reasonable inference.
Do NOT invent specifics that contradict the text.

Raw idea:
\"\"\"{idea}\"\"\"
"""


async def extract_schema(idea_text: str) -> IdeaSchema:
    """Return a structured IdeaSchema from unstructured idea text."""
    prompt = _PROMPT_TEMPLATE.format(idea=idea_text)
    return await call_llm_structured(prompt, IdeaSchema)