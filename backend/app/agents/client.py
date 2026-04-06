import os
from openai import OpenAI
from app.core.config import settings

# Single shared client — all agents import this
# Uses GitHub Models API for free GPT-4o access
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=settings.GITHUB_TOKEN,
)


def call_gpt4o(system_prompt: str, user_message: str, max_tokens: int = 1000) -> str:
    """
    Single function all agents use to call GPT-4o.
    Returns the raw text response.
    Always requests JSON output.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
        temperature=0.1,  # low temperature = more consistent JSON output
    )
    return response.choices[0].message.content