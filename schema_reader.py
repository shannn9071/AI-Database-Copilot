"""
schema_reader.py
------------------
Reads the PostgreSQL database's structure (tables, columns, data types,
primary keys, foreign keys) so the AI engine can be given an accurate,
minimal description of the schema instead of guessing at table/column
names.

Phase 2 scope:
- get_full_schema()     -> the whole schema as a structured dict
- get_schema_text()     -> the whole schema rendered as compact text
                            (what we'll feed the LLM as a default)
- get_relevant_schema_text(question) -> a smaller, filtered version that
                            only includes tables whose name (or a column
                            name) is mentioned in the user's question.
                            This keeps prompts short and accurate once
                            we wire up the AI engine in Phase 3.

We use SQLAlchemy's `inspect()` API rather than raw SQL against
`information_schema`, because it already normalizes PK/FK info across
databases and is less error-prone for a student project.
"""

from dataclasses import dataclass, field

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from database import get_engine


@dataclass
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    is_primary_key: bool = False


@dataclass
class ForeignKeyInfo:
    column: str                # column in this table
    references_table: str      # table it points to
    references_column: str     # column it points to


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = field(default_factory=list)


def get_full_schema(engine: Engine | None = None, schema: str = "public") -> list[TableInfo]:
    """
    Inspect the database and return structured metadata for every table
    in the given Postgres schema (default: "public").
    """
    engine = engine or get_engine()
    inspector = inspect(engine)

    tables: list[TableInfo] = []

    for table_name in inspector.get_table_names(schema=schema):
        pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
        pk_columns = set(pk_constraint.get("constrained_columns") or [])

        columns = [
            ColumnInfo(
                name=col["name"],
                type=str(col["type"]),
                nullable=col["nullable"],
                is_primary_key=col["name"] in pk_columns,
            )
            for col in inspector.get_columns(table_name, schema=schema)
        ]

        foreign_keys = [
            ForeignKeyInfo(
                column=fk["constrained_columns"][0],
                references_table=fk["referred_table"],
                references_column=fk["referred_columns"][0],
            )
            for fk in inspector.get_foreign_keys(table_name, schema=schema)
            if fk.get("constrained_columns") and fk.get("referred_columns")
        ]

        tables.append(TableInfo(name=table_name, columns=columns, foreign_keys=foreign_keys))

    return tables


def _render_table(table: TableInfo) -> str:
    """Render one TableInfo as compact text, e.g.:

    Table: orders
      - order_id (INTEGER, PK)
      - customer_id (INTEGER, FK -> customers.customer_id)
      - order_date (DATE)
      - status (VARCHAR)
    """
    lines = [f"Table: {table.name}"]
    fk_by_column = {fk.column: fk for fk in table.foreign_keys}

    for col in table.columns:
        tags = []
        if col.is_primary_key:
            tags.append("PK")
        if col.name in fk_by_column:
            fk = fk_by_column[col.name]
            tags.append(f"FK -> {fk.references_table}.{fk.references_column}")
        tag_str = f", {', '.join(tags)}" if tags else ""
        lines.append(f"  - {col.name} ({col.type}{tag_str})")

    return "\n".join(lines)


def get_schema_text(engine: Engine | None = None, schema: str = "public") -> str:
    """Render the full schema as compact text, suitable for an LLM prompt."""
    tables = get_full_schema(engine, schema)
    if not tables:
        return "(no tables found)"
    return "\n\n".join(_render_table(t) for t in tables)


def get_relevant_schema_text(
    question: str,
    engine: Engine | None = None,
    schema: str = "public",
) -> str:
    """
    Return a filtered schema description that only includes tables which
    seem relevant to the user's question — either the table name itself
    or one of its column names appears in the question (case-insensitive,
    matching on singular/plural word stems loosely).

    Falls back to the full schema if nothing matches, so we never send
    the LLM an empty/blank schema.

    This is a simple heuristic for now. In Phase 3, when we wire up the
    AI engine, this is the function `ai_engine.py` will call before
    building the prompt — keeping token usage down and improving
    accuracy by not showing the LLM irrelevant tables.
    """
    tables = get_full_schema(engine, schema)
    question_lower = question.lower()

    def table_is_relevant(table: TableInfo) -> bool:
        # Match table name (singular or plural form)
        name = table.name.lower()
        if name in question_lower or name.rstrip("s") in question_lower:
            return True
        # Match any column name
        for col in table.columns:
            if col.name.lower() in question_lower:
                return True
        return False

    relevant = [t for t in tables if table_is_relevant(t)]

    if not relevant:
        # Nothing matched — safer to give the AI the whole schema than
        # to give it nothing.
        relevant = tables

    if not relevant:
        return "(no tables found)"

    return "\n\n".join(_render_table(t) for t in relevant)


if __name__ == "__main__":
    # Quick manual test: run `python schema_reader.py` from the terminal.
    print("=== Full schema ===")
    print(get_schema_text())

    print("\n=== Relevant schema for a sample question ===")
    sample_question = "Who are the top customers by total spending?"
    print(f'Question: "{sample_question}"\n')
    print(get_relevant_schema_text(sample_question))
