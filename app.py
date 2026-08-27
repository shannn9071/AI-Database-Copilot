"""
app.py
-------
Streamlit frontend for AI Database Copilot.

Phase 1 scope:
- Page setup (title, layout)
- A "Database connection status" indicator, using database.test_connection()
- Placeholders for the pieces we'll build in later phases
  (question input, clarification UI, SQL/results display, history sidebar)

Run with:  streamlit run app.py
"""

import streamlit as st
from database import test_connection, execute_query, QueryExecutionError
from schema_reader import get_schema_text
from ai_engine import get_ai_response, AIEngineError
from clarification import build_clarified_question
from sql_validator import validate_sql
from history import add_entry, update_entry, load_history, clear_history

st.set_page_config(
    page_title="AI Database Copilot",
    page_icon="🗄️",
    layout="wide",
)

# ---------- Sidebar: Query History ----------
_STATUS_ICONS = {
    "generated": "📝",
    "success": "✅",
    "no_results": "🈳",
    "error": "❌",
    "blocked": "🚫",
}

with st.sidebar:
    st.header("📜 Query History")
    history_entries = load_history()

    if not history_entries:
        st.caption("Your past questions will appear here once you ask something.")
    else:
        if st.button("🗑️ Clear history"):
            clear_history()
            st.rerun()

        for entry in reversed(history_entries):
            icon = _STATUS_ICONS.get(entry.status, "•")
            label = entry.question if len(entry.question) <= 50 else entry.question[:47] + "..."
            with st.expander(f"{icon} {label}"):
                st.caption(entry.timestamp)
                if entry.clarification_question:
                    st.markdown(f"**Clarification:** {entry.clarification_question}")
                    st.markdown(f"**Answer:** {entry.clarification_answer}")
                if entry.sql_query:
                    st.code(entry.sql_query, language="sql")
                st.caption(f"Status: {entry.status}")

# ---------- Header ----------
st.title("🗄️ AI Database Copilot")
st.caption("Ask questions about your database in plain English.")

# ---------- Database connection status ----------
st.subheader("1. Database Connection Status")

col1, col2 = st.columns([1, 4])
with col1:
    check = st.button("Check connection")

if check:
    with st.spinner("Connecting to PostgreSQL..."):
        ok, message = test_connection()
    if ok:
        st.success(message)
    else:
        st.error(message)
else:
    st.info("Click 'Check connection' to verify your database is reachable.")

st.divider()

# ---------- Database schema viewer ----------
st.subheader("2. Database Schema")
with st.expander("View detected schema", expanded=False):
    if st.button("Load schema"):
        with st.spinner("Reading schema from PostgreSQL..."):
            try:
                schema_text = get_schema_text()
                st.code(schema_text, language="text")
            except Exception as exc:
                st.error(f"Could not read schema: {exc}")
    else:
        st.caption("Click 'Load schema' to inspect tables, columns, and relationships.")

st.divider()

# ---------- Session state ----------
# pending_response: an AIQueryResponse waiting on a clarification answer
# original_question: the question that produced pending_response
# final_response: the AIQueryResponse ready to display (SQL + explanation)
# last_question / last_sql: the most recent successfully-generated
#   question/SQL pair, carried across questions so a new question can be
#   treated as a follow-up refinement. NOT cleared by _reset_flow —
#   only by the explicit "New topic" button below.
for key in (
    "pending_response", "original_question", "final_response",
    "last_result_df", "current_history_index", "last_question", "last_sql",
):
    if key not in st.session_state:
        st.session_state[key] = None


def _reset_flow():
    st.session_state.pending_response = None
    st.session_state.original_question = None
    st.session_state.final_response = None
    st.session_state.last_result_df = None
    st.session_state.current_history_index = None


# ---------- Natural language question input ----------
st.subheader("3. Ask a question")

if st.session_state.last_question:
    ctx_col1, ctx_col2 = st.columns([5, 1])
    with ctx_col1:
        st.caption(f"🔗 Continuing from: \"{st.session_state.last_question}\" — new questions may refine this.")
    with ctx_col2:
        if st.button("🆕 New topic"):
            st.session_state.last_question = None
            st.session_state.last_sql = None
            st.rerun()

question = st.text_input(
    "Type your question about the database",
    placeholder='e.g. "Show me the best customers"',
    key="question_input",
)

if st.button("Submit question", type="primary") and question.strip():
    _reset_flow()
    st.session_state.original_question = question.strip()
    try:
        with st.spinner("Thinking..."):
            schema_text = get_schema_text()
            response = get_ai_response(
                question.strip(),
                schema_text,
                previous_question=st.session_state.last_question,
                previous_sql=st.session_state.last_sql,
            )
        if response.is_ambiguous:
            st.session_state.pending_response = response
        else:
            st.session_state.final_response = response
            st.session_state.current_history_index = add_entry(
                question=st.session_state.original_question,
                status="generated",
                sql_query=response.sql_query,
            )
            st.session_state.last_question = st.session_state.original_question
            st.session_state.last_sql = response.sql_query
    except AIEngineError as exc:
        st.error(str(exc))

# ---------- Clarification UI ----------
if st.session_state.pending_response is not None:
    pending = st.session_state.pending_response
    st.info(f"🤔 {pending.clarification_question}")

    chosen_option = st.radio(
        "Choose the closest match:",
        options=pending.clarification_options or [],
        key="clarification_choice",
    )

    if st.button("Continue with this answer"):
        clarified_question = build_clarified_question(
            st.session_state.original_question,
            pending.clarification_question,
            chosen_option,
        )
        try:
            with st.spinner("Generating SQL..."):
                schema_text = get_schema_text()
                final = get_ai_response(clarified_question, schema_text)
            st.session_state.pending_response = None
            if final.is_ambiguous:
                # Still ambiguous after one round of clarification —
                # show it again rather than looping forever.
                st.session_state.pending_response = final
            else:
                st.session_state.final_response = final
                st.session_state.last_result_df = None
                st.session_state.current_history_index = add_entry(
                    question=st.session_state.original_question,
                    status="generated",
                    clarification_question=pending.clarification_question,
                    clarification_answer=chosen_option,
                    sql_query=final.sql_query,
                )
                st.session_state.last_question = clarified_question
                st.session_state.last_sql = final.sql_query
        except AIEngineError as exc:
            st.error(str(exc))

st.divider()

# ---------- Results: validation, execution, and results table ----------
st.subheader("4. Results")

if st.session_state.final_response is not None:
    final = st.session_state.final_response
    st.markdown("**Generated SQL**")
    st.code(final.sql_query, language="sql")
    st.markdown("**Explanation**")
    st.write(final.explanation)

    is_safe, reason = validate_sql(final.sql_query)

    if not is_safe:
        st.error(f"🚫 This query was blocked before execution: {reason}")
        if st.session_state.current_history_index is not None:
            update_entry(st.session_state.current_history_index, status="blocked")
    else:
        if st.button("▶️ Run query"):
            try:
                with st.spinner("Running query..."):
                    df = execute_query(final.sql_query)
                st.session_state.last_result_df = df
                if st.session_state.current_history_index is not None:
                    new_status = "success" if not df.empty else "no_results"
                    update_entry(st.session_state.current_history_index, status=new_status)
            except QueryExecutionError as exc:
                st.session_state.last_result_df = None
                st.error(str(exc))
                if st.session_state.current_history_index is not None:
                    update_entry(st.session_state.current_history_index, status="error")

        if st.session_state.get("last_result_df") is not None:
            df = st.session_state.last_result_df
            st.markdown("**Query results**")
            if df.empty:
                st.warning("The query ran successfully but returned no rows.")
            else:
                st.dataframe(df, use_container_width=True)
                st.caption(f"📊 {len(df)} row{'s' if len(df) != 1 else ''} returned.")
else:
    st.caption("Ask a question above to see generated SQL, its explanation, and results here.")
