import json
from typing import Any

from backend.app.config import get_settings
from backend.app.services.mock_data import mock_analysis, synthetic_cases


ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {"type": "string"},
        "root_cause": {"type": "string"},
        "suggested_fix": {"type": "string"},
        "confidence": {"type": "number"},
        "status": {"type": "string"},
        "reasoning_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "category",
        "root_cause",
        "suggested_fix",
        "confidence",
        "status",
        "reasoning_notes",
    ],
}


SEED_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "cases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "stack_trace": {"type": "string"},
                    "severity": {"type": "string"},
                    "environment": {"type": "string"},
                    "test_name": {"type": "string"},
                    "suite": {"type": "string"},
                    "failure_signature": {"type": "string"},
                    "root_cause": {"type": "string"},
                    "fix_hint": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": [
                    "title",
                    "description",
                    "stack_trace",
                    "severity",
                    "environment",
                    "test_name",
                    "suite",
                    "failure_signature",
                    "root_cause",
                    "fix_hint",
                    "category",
                ],
            },
        }
    },
    "required": ["cases"],
}


def _client():
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai

        return genai.Client(api_key=settings.gemini_api_key)
    except Exception:
        return None


def _parse_json_response(response: Any) -> dict[str, Any]:
    text = getattr(response, "text", None)
    if not text:
        candidates = getattr(response, "candidates", [])
        if candidates:
            parts = candidates[0].content.parts
            text = "".join(getattr(part, "text", "") for part in parts)
    if not text:
        raise ValueError("Gemini returned an empty response")
    return json.loads(text)


def analyze_bug(bug: dict[str, Any], matches: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    client = _client()
    if client is None:
        if settings.enable_mock_fallback:
            return mock_analysis(bug["title"], matches)
        raise RuntimeError("Gemini client is unavailable and mock fallback is disabled")

    prompt = {
        "instruction": "Analyze the customer bug against matched CI failures. Return strict JSON only.",
        "customer_bug": bug,
        "matched_failures": matches,
    }
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=json.dumps(prompt),
            config={
                "response_mime_type": "application/json",
                "response_schema": ANALYSIS_SCHEMA,
                "temperature": 0.2,
            },
        )
        data = _parse_json_response(response)
        data["used_fallback"] = False
        return data
    except Exception:
        if settings.enable_mock_fallback:
            return mock_analysis(bug["title"], matches)
        raise


def generate_seed_cases(count: int) -> list[dict[str, Any]]:
    settings = get_settings()
    client = _client()
    if client is None:
        if settings.enable_mock_fallback:
            return synthetic_cases(count)
        raise RuntimeError("Gemini client is unavailable and mock fallback is disabled")

    prompt = (
        f"Generate {count} realistic paired customer bug reports and CI test failures "
        "for a developer support triage demo. Include varied categories and stack traces."
    )
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": SEED_SCHEMA,
                "temperature": 0.8,
            },
        )
        data = _parse_json_response(response)
        cases = data.get("cases", [])
        return cases[:count] if len(cases) >= count else cases + synthetic_cases(count - len(cases))
    except Exception:
        if settings.enable_mock_fallback:
            return synthetic_cases(count)
        raise
