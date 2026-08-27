"""
ai_engine.py
-------------
Talks to the LLM (Groq, by default) and returns a validated
AIQueryResponse (see models.py).

Why Groq: it has a generous free tier, is fast, and its API is
OpenAI-compatible, which makes this file easy to read even if you've
only used other LLM SDKs before. If you'd rather use Gemini, only this
file needs to change — everything else (prompts.py, models.py,
clarification.py, app.py) is provider-agnostic.

Setup:
1. Get a free API key from https://console.groq.com/keys
2. Put it in your .env file as GROQ_API_KEY=...
3. pip install groq  (already in requirements.txt)
"""

import json
import os

from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError

from models import AIQueryResponse
from prompts import SYSTEM_PROMPT, build_user_prompt

load_dotenv()

# llama-3.3-70b-versatile was deprecated by Groq — openai/gpt-oss-120b is
# their recommended general-purpose replacement as of mid-2026. If this
# model is retired by the time you read this, check
# https://console.groq.com/docs/models for the current list of
# supported models and swap it in here. openai/gpt-oss-20b is a
# smaller/faster alternative if you want lower latency.
MODEL_NAME = "openai/gpt-oss-120b"


class AIEngineError(Exception):
    """Raised when the AI response can't be obtained or doesn't match
    our expected structure, so the Streamlit app can show a clear
    error instead of crashing."""


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise AIEngineError(
            "GROQ_API_KEY is not set. Add it to your .env file — "
            "see .env.example and https://console.groq.com/keys"
        )
    return Groq(api_key=api_key)


def _strip_code_fences(text: str) -> str:
    """Some models wrap JSON in ```json ... ``` even when told not to.
    Strip that off defensively before parsing."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1] if text.count("```") >= 2 else text.strip("`")
        text = text.removeprefix("json").strip()
    return text.strip()


def get_ai_response(
    question: str,
    schema_text: str,
    previous_question: str | None = None,
    previous_sql: str | None = None,
) -> AIQueryResponse:
    """
    Send the question + relevant schema to the LLM and return a
    validated AIQueryResponse.

    Pass `previous_question` / `previous_sql` — the last successfully
    generated question/SQL pair in this session — to let the model
    treat `question` as a possible follow-up refinement (e.g. "only
    show ones from Delhi") rather than an unrelated new request. Omit
    them to always treat the question as brand new.

    Raises AIEngineError with a human-readable message on any failure
    (missing API key, network error, malformed response, etc.) so the
    caller can display it directly in the Streamlit UI.
    """
    client = _get_client()
    user_prompt = build_user_prompt(question, schema_text, previous_question, previous_sql)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        raise AIEngineError(f"Could not reach the AI service: {exc}") from exc

    raw_content = completion.choices[0].message.content or ""
    cleaned = _strip_code_fences(raw_content)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIEngineError(
            f"AI response wasn't valid JSON: {exc}\n\nRaw response:\n{raw_content}"
        ) from exc

    try:
        return AIQueryResponse.model_validate(data)
    except ValidationError as exc:
        raise AIEngineError(
            f"AI response didn't match the expected structure: {exc}"
        ) from exc


if __name__ == "__main__":
    # Quick manual test: run `python ai_engine.py` from the terminal.
    # Requires a real GROQ_API_KEY in .env and a working DB connection
    # (schema_reader talks to the DB to build the schema text).
    from schema_reader import get_relevant_schema_text

    sample_question = "Show me the best customers."
    schema_text = get_relevant_schema_text(sample_question)

    print(f'Question: "{sample_question}"\n')
    response = get_ai_response(sample_question, schema_text)
    print(response.model_dump_json(indent=2))
