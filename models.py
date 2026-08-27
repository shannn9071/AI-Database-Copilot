"""
models.py
----------
Pydantic models that enforce structured output from the LLM.

Instead of trusting the AI to return well-formed, predictable JSON, we
ask it to produce JSON matching this schema, then validate the response
against `AIQueryResponse`. If the AI's output doesn't match, Pydantic
raises a clear validation error instead of the app breaking silently
or executing something malformed.
"""

from pydantic import BaseModel, Field, model_validator


class AIQueryResponse(BaseModel):
    """
    The structured response we ask the LLM to produce for every
    question. Exactly one of these two situations is true:

    1. The question is ambiguous -> is_ambiguous=True, and
       clarification_question / clarification_options are filled in.
       sql_query / explanation are left empty.

    2. The question is clear -> is_ambiguous=False, and
       sql_query / explanation are filled in. Clarification fields are
       left empty.
    """

    is_ambiguous: bool = Field(
        description="True if the question is too vague to safely generate SQL from."
    )
    clarification_question: str | None = Field(
        default=None,
        description="A question to ask the user, only set when is_ambiguous is True.",
    )
    clarification_options: list[str] | None = Field(
        default=None,
        description="2-5 selectable options for the clarification question.",
    )
    sql_query: str | None = Field(
        default=None,
        description="A single safe, read-only PostgreSQL SELECT statement.",
    )
    explanation: str | None = Field(
        default=None,
        description="A short, plain-English explanation of what the SQL query does.",
    )

    @model_validator(mode="after")
    def check_fields_match_ambiguity(self) -> "AIQueryResponse":
        """Sanity-check that the AI filled in the fields that make sense
        for whichever branch (ambiguous vs. clear) it claims to be in."""
        if self.is_ambiguous:
            if not self.clarification_question:
                raise ValueError(
                    "is_ambiguous=True but clarification_question is missing."
                )
        else:
            if not self.sql_query:
                raise ValueError(
                    "is_ambiguous=False but sql_query is missing."
                )
        return self


class QueryHistoryEntry(BaseModel):
    """
    One row of query history.

    Not used yet (query history UI is Phase 5) — defined now so
    ai_engine.py and app.py can already import a stable shape for it
    as we build toward that phase.
    """

    question: str
    clarification_question: str | None = None
    clarification_answer: str | None = None
    sql_query: str | None = None
    status: str  # e.g. "success", "clarification_needed", "error"
    timestamp: str
