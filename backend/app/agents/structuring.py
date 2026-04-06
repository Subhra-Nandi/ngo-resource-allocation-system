import json
from app.agents.client import call_gpt4o

STRUCTURE_PROMPT = """
You are an AI agent that extracts structured information from NGO field reports.

Extract ONLY what is explicitly mentioned. Return ONLY valid JSON, no explanation.

Output this exact schema:
{
  "location_name": "place name mentioned or null",
  "need_type": "one of: FOOD, MEDICAL, SHELTER, WASH, OTHER",
  "severity": "integer 1-5 (5=most critical) based on urgency words",
  "affected_count": "integer number of people affected or null",
  "description": "one clear sentence summarizing the situation",
  "is_user_request": true or false (true if person needs help NOW, false if field worker reporting),
  "confidence": "float 0.0-1.0 indicating how clear the information is"
}

Severity guide:
1 = minor inconvenience
2 = moderate issue
3 = serious problem
4 = urgent/critical
5 = life-threatening emergency

need_type guide:
FOOD = hunger, food, water, ration, meals
MEDICAL = sick, injured, medicine, hospital, doctor
SHELTER = homeless, flood damage, roof, tent, displaced
WASH = sanitation, toilet, hygiene, clean water
OTHER = anything else
"""


def structure_report(raw_text: str) -> dict:
    """
    Takes normalized text and returns structured data.
    This is the core AI call — text in, clean JSON out.
    """
    if not raw_text or len(raw_text.strip()) < 5:
        return {
            "location_name": None,
            "need_type": "OTHER",
            "severity": 1,
            "affected_count": None,
            "description": raw_text,
            "is_user_request": True,
            "confidence": 0.1,
        }

    result = call_gpt4o(STRUCTURE_PROMPT, raw_text)
    parsed = json.loads(result)

    # Ensure severity is int in range 1-5
    parsed["severity"] = max(1, min(5, int(parsed.get("severity", 3))))

    # Ensure confidence is float in range 0-1
    parsed["confidence"] = max(0.0, min(1.0, float(parsed.get("confidence", 0.5))))

    return parsed