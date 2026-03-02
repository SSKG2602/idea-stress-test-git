"""
services/llm.py — Structured LLM client.

Design contract:
  - Every call returns a validated Pydantic model, never raw text.
  - On invalid JSON or schema mismatch, retries up to llm_max_retries
    with a corrective prompt that includes the validation error.
  - Temperature is hardcoded low (0.2) to maximise determinism.
"""
import json
from typing import TypeVar, Type

import httpx
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from pydantic import BaseModel, ValidationError

from config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when the LLM fails to produce a valid response after retries."""


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_json_system_prompt(schema_example: str) -> str:
    """System prompt that forces the model to return only valid JSON."""
    return (
        "You are a precise business analysis AI. "
        "Respond ONLY with a valid JSON object that exactly matches the schema below. "
        "No markdown, no explanation, no extra keys, no trailing commas. "
        "Do NOT return JSON Schema metadata such as $defs, properties, required, type, minimum, maximum, or title.\n\n"
        f"Required schema:\n{schema_example}"
    )


def _decode_json_objects(text: str) -> list[dict]:
    """
    Decode JSON object candidates found in `text`.
    Handles LLM outputs that append prose, fences, or multiple JSON objects.
    """
    decoder = json.JSONDecoder()
    candidate = text.strip()
    objects: list[dict] = []

    def _add_if_object(obj) -> None:
        if isinstance(obj, dict):
            objects.append(obj)

    def _decode_stream(chunk: str) -> None:
        i = 0
        n = len(chunk)
        while i < n:
            start = chunk.find("{", i)
            if start == -1:
                break
            try:
                obj, end = decoder.raw_decode(chunk[start:])
                _add_if_object(obj)
                i = start + end
            except json.JSONDecodeError:
                i = start + 1

    # Decode top-level stream from raw output.
    _decode_stream(candidate)

    # If model wrapped output in markdown fences, decode fenced payload streams too.
    if candidate.startswith("```"):
        for part in candidate.split("```"):
            chunk = part.strip()
            if not chunk:
                continue
            if chunk.lower().startswith("json"):
                chunk = chunk[4:].strip()
            _decode_stream(chunk)

    # Dedupe while preserving order.
    deduped: list[dict] = []
    seen: set[str] = set()
    for obj in objects:
        key = json.dumps(obj, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(obj)

    return deduped


def _looks_like_schema_object(obj: dict) -> bool:
    """
    Heuristic: LLM returned a JSON Schema definition instead of an instance object.
    """
    schema_keys = {
        "$defs", "$ref", "properties", "required", "title",
        "description", "items", "anyOf", "allOf", "oneOf",
        "type", "minimum", "maximum", "enum",
    }
    obj_keys = set(obj.keys())
    if "$defs" in obj_keys or "$ref" in obj_keys:
        return True
    if "properties" in obj_keys and obj.get("type") == "object":
        return True
    # Fragments like {"type":"integer","minimum":1,"maximum":5,"value":4}
    if ("type" in obj_keys) and obj_keys.issubset(schema_keys | {"value", "default", "examples"}):
        return True
    return False


async def _call_llm(
    system: str,
    user: str,
    client: httpx.AsyncClient,
) -> str:
    """Raw HTTP call to OpenAI-compatible /chat/completions endpoint."""
    payload = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    }
    resp = await client.post(
        f"{settings.llm_base_url}/chat/completions",
        json=payload,
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


# ── Public interface ──────────────────────────────────────────────────────────

async def call_llm_structured(
    user_prompt: str,
    output_schema: Type[T],
    extra_context: str = "",
) -> T:
    """
    Call provider LLM and parse the response into `output_schema`.

    Retry loop:
      1. Call LLM with the schema embedded in the system prompt.
      2. Parse JSON from response.
      3. Validate with Pydantic.
      4. On failure, re-call with the error message so the model can self-correct.
    """
    # Build a compact schema example from the model's JSON schema
    schema_str = json.dumps(output_schema.model_json_schema(), indent=2)
    system = _build_json_system_prompt(schema_str)

    if extra_context:
        user_prompt = f"{extra_context}\n\n---\n\n{user_prompt}"

    last_error: str = ""

    async with httpx.AsyncClient() as client:
        for attempt in range(1, settings.llm_max_retries + 1):
            prompt = user_prompt
            if last_error and attempt > 1:
                # Self-correction: tell the model what went wrong
                prompt = (
                    f"{user_prompt}\n\n"
                    f"[CORRECTION REQUIRED] Your previous response failed validation:\n"
                    f"{last_error}\n"
                    "Return corrected JSON only.\n"
                    "Do not output schema metadata keys like $defs, properties, required, type, minimum, maximum, or title."
                )

            log.info("llm.call", model=settings.llm_model, attempt=attempt,
                     schema=output_schema.__name__)

            try:
                raw = await _call_llm(system, prompt, client)
                candidates = _decode_json_objects(raw)
                if not candidates:
                    raise json.JSONDecodeError("No valid JSON object found", raw, 0)

                last_validation_error: ValidationError | None = None
                schema_like_count = 0

                for parsed_dict in candidates:
                    if _looks_like_schema_object(parsed_dict):
                        schema_like_count += 1
                        continue
                    try:
                        result = output_schema.model_validate(parsed_dict)
                        log.info(
                            "llm.success",
                            schema=output_schema.__name__,
                            attempt=attempt,
                        )
                        return result
                    except ValidationError as validation_error:
                        last_validation_error = validation_error

                if schema_like_count > 0:
                    raise ValueError(
                        "Model returned schema-like JSON instead of a populated answer object."
                    )

                if last_validation_error is not None:
                    raise last_validation_error

                raise ValueError("No candidate JSON object matched the expected schema.")

            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON: {e}"
                log.warning("llm.json_error", attempt=attempt, error=last_error)

            except ValidationError as e:
                last_error = str(e)
                log.warning("llm.validation_error", attempt=attempt, error=last_error)

            except ValueError as e:
                last_error = str(e)
                log.warning("llm.content_error", attempt=attempt, error=last_error)

            except httpx.HTTPStatusError as e:
                response_text = e.response.text.strip()
                # Keep logs readable while preserving the key API error details.
                response_excerpt = response_text[:500] if response_text else ""
                log.error(
                    "llm.http_error",
                    status=e.response.status_code,
                    response_body=response_excerpt,
                )
                raise LLMError(
                    f"LLM API HTTP {e.response.status_code}"
                    + (f": {response_excerpt}" if response_excerpt else "")
                ) from e

    raise LLMError(
        f"Failed to get valid {output_schema.__name__} after "
        f"{settings.llm_max_retries} attempts. Last error: {last_error}"
    )
