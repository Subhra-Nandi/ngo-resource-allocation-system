import json
from app.agents.client import call_gpt4o

VALIDATION_PROMPT = """
You are a validation agent for an NGO disaster relief platform.

Assess if this help request is genuine and disaster/emergency related.

Return ONLY valid JSON:
{
  "is_valid": true or false,
  "confidence": float 0.0 to 1.0,
  "reason": "one short sentence explaining the decision"
}

Mark is_valid as FALSE if:
- It looks like a test message (e.g. "test", "hello", "abc")
- It is clearly spam or gibberish
- It is not related to disaster, emergency, or humanitarian need

Mark is_valid as TRUE if:
- It describes a genuine emergency or humanitarian need
- It mentions affected people, location, or specific resources needed
- Even if poorly written — give benefit of the doubt for real emergencies
"""


def validate_need(description: str) -> dict:
    """
    Validation Gate 1 — checks if the request is genuine.
    Returns {is_valid, confidence, reason}
    """
    if not description or len(description.strip()) < 5:
        return {
            "is_valid": False,
            "confidence": 0.95,
            "reason": "Description too short to be a valid request",
        }

    result = call_gpt4o(
        VALIDATION_PROMPT,
        f"Help request: {description}",
        max_tokens=200,
    )
    parsed = json.loads(result)
    parsed["confidence"] = max(0.0, min(1.0, float(parsed.get("confidence", 0.5))))
    return parsed