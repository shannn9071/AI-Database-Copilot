"""
database.py
-------------
Handles the PostgreSQL connection and (later) query execution.

Phase 1 scope:
- Build a SQLAlchemy engine from environment variables
- Provide a simple `test_connection()` helper the Streamlit app can call
  to show a green/red connection status badge.

Later phases will add `execute_query()` for running validated SELECT
statements and returning results as a pandas DataFrame.
"""

import os
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Load variables from .env into the environment
load_dotenv()


def get_db_config() -> dict:
    """Read DB connection settings from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "name": os.getenv("DB_NAME", "ai_copilot_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def build_connection_url(config: dict | None = None) -> str:
    """Build a SQLAlchemy connection URL for PostgreSQL using psycopg (v3).

    The username and password are URL-encoded with quote_plus() so
    special characters (@, :, /, #, etc. — common in real passwords)
    don't get misread as part of the URL's structure.
    """
    cfg = config or get_db_config()
    user = quote_plus(cfg["user"])
    password = quote_plus(cfg["password"])
    return (
        f"postgresql+psycopg://{user}:{password}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['name']}"
    )


def get_engine() -> Engine:
    """Create (once) and return a SQLAlchemy engine for the configured database."""
    url = build_connection_url()
    # pool_pre_ping checks the connection is alive before using it —
    # helpful for long-running Streamlit sessions.
    engine = create_engine(url, pool_pre_ping=True)
    return engine


class QueryExecutionError(Exception):
    """Raised by execute_query() with a human-readable message, so the
    Streamlit UI can display it directly instead of a raw traceback."""


def execute_query(sql: str) -> pd.DataFrame:
    """
    Execute an already-validated, read-only SQL query and return the
    results as a pandas DataFrame.

    IMPORTANT: this function does not itself check that the SQL is
    safe — callers must run it through sql_validator.validate_sql()
    first. Keeping validation and execution as separate steps makes
    each easier to test and reason about on its own.

    Raises QueryExecutionError with a clear message for:
        - invalid SQL syntax
        - missing tables/columns
        - database connection errors
    Returns an empty DataFrame (not an error) when the query runs fine
    but simply matches zero rows.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())
        return pd.DataFrame(rows, columns=columns)
    except SQLAlchemyError as exc:
        # SQLAlchemy wraps the underlying psycopg error; the original
        # database message (e.g. "column X does not exist") is usually
        # in str(exc.orig) and is more useful to show than the full
        # SQLAlchemy wrapper text.
        original = getattr(exc, "orig", None)
        detail = str(original) if original else str(exc)
        raise QueryExecutionError(f"Query failed: {detail.strip()}") from exc
    except Exception as exc:
        raise QueryExecutionError(f"Unexpected error running query: {exc}") from exc


def test_connection() -> tuple[bool, str]:
    """
    Try to connect to the database and run a trivial query.

    Returns:
        (success: bool, message: str)
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
        return True, f"Connected successfully. PostgreSQL version: {version}"
    except Exception as exc:
        return False, f"Connection failed: {exc}"


if __name__ == "__main__":
    # Quick manual test: run `python database.py` from the terminal.
    ok, msg = test_connection()
    print("✅" if ok else "❌", msg)
