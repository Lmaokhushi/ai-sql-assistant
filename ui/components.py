"""
Pieces of the interface: landing page, the "How it works" guide,
chat messages, result tables and schema tables.
"""

import html

import pandas as pd
import streamlit as st

from config import APP_NAME, APP_TAGLINE, MAX_RESULT_ROWS

# ---- Icons (inline SVG so they follow the text colour in both themes) -------

def _svg(paths, size=22, stroke=1.9):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{paths}</svg>'
    )

ICON_LOGO = _svg('<path d="M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3z"/>', size=20, stroke=2)
ICON_DATABASE = _svg('<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3"/>')
ICON_TABLE = _svg('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 10v10M15 10v10"/>')
ICON_SPARK = _svg('<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/>', size=14, stroke=2.2)


def esc(text):
    return html.escape(str(text))


# ---- Landing page ------------------------------------------------------------

def render_setup_warning():
    st.markdown("""
    <div class="qp-setup">
        <b>⚠️ One step before you start: add your Gemini API key</b>
        <ol>
            <li>Get a free key at <a href="https://aistudio.google.com/apikey" target="_blank">aistudio.google.com/apikey</a>.</li>
            <li>Open the <span class="qp-inline-code">.env</span> file in the project folder.</li>
            <li>Paste the key after <span class="qp-inline-code">GEMINI_API_KEY=</span> and save the file.</li>
            <li>Refresh this page. The status in the sidebar turns green.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


def render_hero():
    st.markdown(f"""
    <div class="qp-hero">
        <div class="qp-badge">{ICON_SPARK} AI-powered SQL assistant</div>
        <h1>Talk to your data.<br><span class="qp-gradient">Skip the SQL headaches.</span></h1>
        <p>{esc(APP_TAGLINE)}</p>
    </div>
    """, unsafe_allow_html=True)


def render_steps():
    st.markdown("""
    <div class="qp-steps">
        <div class="qp-step"><div class="qp-step-num">1</div>
            <div><b>Add your data</b><span>Upload CSV files, or paste or describe your database tables.</span></div></div>
        <div class="qp-step"><div class="qp-step-num">2</div>
            <div><b>Ask in plain English</b><span>"Which products sold best last month?" No SQL needed.</span></div></div>
        <div class="qp-step"><div class="qp-step-num">3</div>
            <div><b>Get checked SQL &amp; answers</b><span>Every query is validated. With CSVs you also see real results.</span></div></div>
    </div>
    """, unsafe_allow_html=True)


def render_path_cards(on_sample_schema, on_sample_data):
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown(f"""
        <div class="qp-card">
            <div class="qp-card-icon">{ICON_DATABASE}</div>
            <h4>I have a database</h4>
            <p>Paste your <code>CREATE TABLE</code> statements, or simply describe your tables
            in the chat. You'll get SQL written for your dialect (MySQL, PostgreSQL, and more).</p>
            <ul>
                <li>Refine queries by chatting: "add a filter for 2025"</li>
                <li>Paste an error message to get it explained and fixed</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.button("Try a sample schema", icon=":material/schema:", width="stretch",
                  on_click=on_sample_schema, key="cta_schema")
    with col2:
        st.markdown(f"""
        <div class="qp-card">
            <div class="qp-card-icon">{ICON_TABLE}</div>
            <h4>I have spreadsheets</h4>
            <p>Upload one or more CSV files in the sidebar. {esc(APP_NAME)} turns them into tables,
            writes the SQL and <b>runs it on your actual data</b>, so you see the answer.</p>
            <ul>
                <li>Each file becomes a table, and columns are detected automatically</li>
                <li>Download any result as a CSV</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.button("Try sample sales data", icon=":material/table_chart:", width="stretch",
                  type="primary", on_click=on_sample_data, key="cta_data")


def render_suggestions(questions, on_pick, key_prefix):
    st.markdown('<div class="qp-label">Try asking</div>', unsafe_allow_html=True)
    cols = st.columns(len(questions))
    for i, (col, question) in enumerate(zip(cols, questions)):
        col.button(question, key=f"{key_prefix}_{i}", width="stretch",
                   on_click=on_pick, args=(question,))


# ---- "How it works" guide ----------------------------------------------------

GUIDE_MARKDOWN = f"""
**{APP_NAME}** turns plain-English questions into SQL. There's one chat, and it
works out what you mean from what you give it.

#### 1 · Give it your data (pick one, or both)
- **CSV files:** use **Upload data** in the sidebar. Each file becomes a table
  (`Sales Data.csv` → `sales_data`). Column names are cleaned up and types are detected.
- **An existing database:** paste your `CREATE TABLE` statements into the chat,
  or describe it, for example: *"I have a customers table with customer_id (primary key),
  name and city, and an orders table with order_id, customer_id and amount."*

#### 2 · Ask questions
Type things like *"top 10 customers by revenue"* or *"orders per month in 2025"*.
You'll get:
- the **SQL query**, ready to copy
- a **validation check** that confirms it only reads data and uses real tables and columns
- with CSV data, the **actual results** as a table you can download

#### 3 · Keep the conversation going
- **Refine:** *"now only show London"*, *"sort by date"*, *"use a LEFT JOIN"*
- **Fix errors:** paste the error your database gave you, for example
  `no such column: amnt`, and you'll get an explanation and a corrected query
- **Explain:** *"explain this query"*

#### Your chats are saved
Every chat is saved automatically on this computer, along with its tables, uploaded data
and conversation memory. Reopen it from **Recent chats** and carry on where you left off.
Use **⋯** next to the chat title to rename or delete it.

#### Good to know
- **SQL dialect:** pick yours in the sidebar. With CSV data it's fixed to SQLite,
  because that's what runs the query.
- **Safety:** only read-only `SELECT` queries are allowed. Nothing can modify your data.
- Results show up to {MAX_RESULT_ROWS:,} rows. Always review generated SQL before running
  it on an important database.
"""


@st.dialog("How QueryPilot works", width="large")
def show_guide():
    st.markdown(GUIDE_MARKDOWN)


# ---- Chat header ------------------------------------------------------------

def render_chat_header(title, context, on_rename, on_delete, chat_id):
    left, right = st.columns([0.9, 0.1], vertical_alignment="center")
    chips = []
    if context.has_csv:
        chips.append(f'<span class="qp-chip">📊 {len(context.csv_data["dataframes"])} CSV table(s)</span>')
    if context.user_schema:
        chips.append(f'<span class="qp-chip">🗂️ {len(context.user_schema["tables"])} schema table(s)</span>')
    chips.append(f'<span class="qp-chip">{esc(context.active_dialect.upper())}</span>')
    with left:
        st.markdown(
            f'<div class="qp-chat-title">{esc(title)}</div>'
            f'<div class="qp-chat-sub">{"".join(chips)}</div>',
            unsafe_allow_html=True,
        )
    with right:
        if chat_id:
            with st.popover(":material/more_horiz:", help="Rename or delete this chat"):
                new_title = st.text_input("Rename chat", value=title, key=f"rename_{chat_id}")
                st.button("Save name", width="stretch", on_click=on_rename,
                          args=(new_title,), key=f"save_name_{chat_id}")
                st.divider()
                st.button("Delete chat", icon=":material/delete:", width="stretch",
                          on_click=on_delete, key=f"delete_{chat_id}")


# ---- Messages ---------------------------------------------------------------

def render_schema_table(table):
    rows = []
    for column in table["columns"]:
        key = "🔑 PK" if column.get("primary_key") else ""
        fk = column.get("foreign_key")
        if fk:
            key = (key + "  " if key else "") + f"→ {fk['table']}.{fk['column']}"
        rows.append({"Column": column["name"], "Type": column.get("type", ""), "Key": key})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def render_result(result, key):
    kind = result.get("kind")

    if kind == "error":
        st.error(result["text"], icon=":material/error:")
        return

    st.markdown(result["text"])

    if kind == "schema" and result.get("schema"):
        tables = result["schema"]["tables"]
        if len(tables) == 1:
            render_schema_table(tables[0])
        else:
            tabs = st.tabs([t["name"] for t in tables])
            for tab, table in zip(tabs, tables):
                with tab:
                    render_schema_table(table)

    if result.get("diagnosis"):
        with st.expander("What I found", icon=":material/search:", expanded=True):
            st.markdown(result["diagnosis"])
    if result.get("explanation"):
        with st.expander("What I changed", icon=":material/edit_note:", expanded=not result.get("diagnosis")):
            st.markdown(result["explanation"])

    if result.get("sql"):
        st.code(result["sql"], language="sql")
        _render_validation(result.get("validation"))

    execution = result.get("execution")
    if execution and execution.get("success"):
        _render_execution(execution, key)
    elif execution and not execution.get("skipped"):
        st.warning(f"The query failed when run: {execution.get('error')}", icon=":material/warning:")


def _render_validation(validation):
    if not validation:
        return
    if validation["valid"]:
        st.markdown('<span class="qp-chip qp-ok">✓ Validated: read-only, real tables and columns</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<span class="qp-chip qp-bad">✕ Validation issues</span>', unsafe_allow_html=True)
        for error in validation.get("errors", []):
            st.markdown(f"- {error}")


def _render_execution(execution, key):
    dataframe = execution.get("dataframe")
    chips = [f"⚡ {execution.get('row_count', 0):,} row(s)"]
    if execution.get("execution_time") is not None:
        chips.append(f"⏱ {execution['execution_time']}s")
    chip_html = "".join(f'<span class="qp-chip">{esc(c)}</span>' for c in chips)
    if execution.get("truncated"):
        chip_html += f'<span class="qp-chip qp-warn">Showing first {MAX_RESULT_ROWS:,} rows</span>'
    st.markdown(chip_html, unsafe_allow_html=True)

    if dataframe is not None and not dataframe.empty:
        st.dataframe(dataframe, hide_index=True, width="stretch")
        st.download_button(
            "Download results", dataframe.to_csv(index=False).encode("utf-8"),
            file_name="query_results.csv", mime="text/csv", key=f"dl_{key}",
            icon=":material/download:",
        )
    else:
        st.caption("The query ran successfully but returned no rows.")
