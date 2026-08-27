"""
history.py
-----------
Saves and loads query history to a local JSON file so past interactions
survive restarting the Streamlit app (not just the current session).

Each entry uses the QueryHistoryEntry shape from models.py: the user's
question, the clarification question/answer if one was needed, the
generated SQL, an execution status, and a timestamp.

For a single-user student project, a small JSON file is simpler and more
transparent than adding a second database table — you can open
data/query_history.json directly to see exactly what's stored.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from models import QueryHistoryEntry

HISTORY_FILE = Path(__file__).parent / "data" / "query_history.json"

# Keep the file from growing forever — old entries beyond this count are
# dropped when saving. Plenty for a demo/portfolio project.
MAX_ENTRIES = 200


def _ensure_data_dir() -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_history() -> list[QueryHistoryEntry]:
    """Return all saved history entries, most recent last. Returns an
    empty list if no history file exists yet or it can't be parsed."""
    if not HISTORY_FILE.exists():
        return []
    try:
        raw = json.loads(HISTORY_FILE.read_text())
        return [QueryHistoryEntry.model_validate(item) for item in raw]
    except (json.JSONDecodeError, ValueError):
        # Corrupted file — don't crash the app, just start fresh.
        return []


def _save_all(entries: list[QueryHistoryEntry]) -> None:
    _ensure_data_dir()
    trimmed = entries[-MAX_ENTRIES:]
    HISTORY_FILE.write_text(
        json.dumps([e.model_dump() for e in trimmed], indent=2)
    )


def add_entry(
    question: str,
    status: str,
    clarification_question: str | None = None,
    clarification_answer: str | None = None,
    sql_query: str | None = None,
) -> int:
    """
    Append a new history entry and save it. Returns the entry's index
    within the saved list, so the caller can later update its status
    (e.g. once execution finishes) with update_entry().
    """
    entries = load_history()
    entry = QueryHistoryEntry(
        question=question,
        clarification_question=clarification_question,
        clarification_answer=clarification_answer,
        sql_query=sql_query,
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    entries.append(entry)
    _save_all(entries)
    return len(entries) - 1


def update_entry(index: int, **fields) -> None:
    """
    Update fields on the entry at `index` (as returned by add_entry())
    and re-save. Used to move an entry from status="generated" to
    status="success" / "no_results" / "error" once the query has
    actually been run.
    """
    entries = load_history()
    if 0 <= index < len(entries):
        updated = entries[index].model_copy(update=fields)
        entries[index] = updated
        _save_all(entries)


def clear_history() -> None:
    """Delete all saved history."""
    _save_all([])


if __name__ == "__main__":
    # Quick manual test: run `python history.py`.
    idx = add_entry(
        question="Show me the best customers.",
        status="generated",
        clarification_question="What do you mean by best?",
        clarification_answer="Highest total spending",
        sql_query="SELECT full_name, SUM(...) FROM customers ...",
    )
    print(f"Added entry at index {idx}")
    update_entry(idx, status="success")
    for e in load_history():
        print(e.model_dump_json(indent=2))
