import json
from app.agents.client import call_gpt4o

VALIDATION_PROMPT = """
You are a validation agent for an NGO disaster relief platform in India.

Assess if this help request is related to disaster, emergency, or humanitarian need.
Be GENEROUS — when in doubt, mark as valid. Real emergencies may be poorly written.

Return ONLY valid JSON:
{
  "is_valid": true or false,
  "confidence": float 0.0 to 1.0,
  "reason": "one short sentence"
}

Mark is_valid as FALSE ONLY if:
- It is clearly a test message like "test", "hello", "abc", "1234"
- It is obvious spam or gibberish with no meaning

Mark is_valid as TRUE for EVERYTHING ELSE including:
- Any mention of food, water, medicine, shelter
- Any mention of people needing help
- Any mention of flood, cyclone, disaster, emergency
- Poorly written or short descriptions that could be real
- Non-English text (Bengali, Hindi etc.) — treat as valid
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