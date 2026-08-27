"""
clarification.py
------------------
Helpers for the clarification flow. The LLM makes the actual
is_ambiguous decision (see prompts.py / ai_engine.py) since it can reason
about context the way a simple keyword check can't — but we keep a small
heuristic here too, for two reasons:

1. It's a fast, free, offline "does this look vague?" signal we can show
   in the UI or use for logging/debugging, without an API call.
2. It documents, in one obvious place, the category of words the spec
   calls out ("best", "top", "recent", "high", etc.) so it's easy to
   extend later.

The other job of this module is combining the user's original question
with their clarification answer into a single, unambiguous follow-up
question we can send back to the AI engine to get the final SQL.
"""

VAGUE_TERMS = {
    "best", "top", "recent", "recently", "high", "highest", "low", "lowest",
    "popular", "good", "great", "important", "significant", "large", "small",
    "many", "few", "most", "least", "cheap", "expensive", "new", "old",
}


def contains_vague_language(question: str) -> bool:
    """
    Quick heuristic: does this question contain any word from our vague
    terms list? This is intentionally simple (word-boundary matching on
    lowercased text) — it's a hint, not the final decision. The AI's
    `is_ambiguous` field, informed by the actual schema, is authoritative.
    """
    words = {w.strip(".,?!\"'") for w in question.lower().split()}
    return bool(words & VAGUE_TERMS)


def build_clarified_question(
    original_question: str,
    clarification_question: str,
    chosen_option: str,
) -> str:
    """
    Combine the original question, the clarification question that was
    asked, and the option the user picked, into a single self-contained
    question we can send back to the AI engine. This lets the AI
    generate SQL without needing multi-turn conversation memory.
    """
    return (
        f'{original_question.strip()}\n\n'
        f'(Clarification: "{clarification_question.strip()}" '
        f'— the user chose: "{chosen_option.strip()}")'
    )
