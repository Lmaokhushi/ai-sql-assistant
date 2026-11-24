"""
QueryPilot: AI-powered SQL assistant.

Run with:  streamlit run app.py

This file wires the interface together: session state, the sidebar, saving
and loading chats, and the main chat area. The decisions about each message
live in ai_engine/orchestrator.py. Visual pieces live in ui/.
"""

from pathlib import Path

import streamlit as st

from config import (
    APP_ICON, APP_NAME, DIALECTS, MAX_SAVED_CHATS_SHOWN,
    SAMPLE_DATA_QUESTIONS, SAMPLE_SCHEMA, SCHEMA_QUESTIONS,
)

st.set_page_config(
    page_title=f"{APP_NAME} · AI SQL Assistant",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

from ai_engine.gemini_client import api_key_configured, get_model  # noqa: E402
from ai_engine.orchestrator import AssistantContext, handle_message  # noqa: E402
from data.csv_processor import process_csv_files  # noqa: E402
from ui import components as ui  # noqa: E402
from ui.styles import inject_css  # noqa: E402
from utils import chat_store  # noqa: E402
from utils.conversation_manager import ConversationManager  # noqa: E402
from utils.helpers import make_chat_title, time_ago  # noqa: E402

SAMPLE_DIR = Path(__file__).resolve().parent / "sample_data"


# =============================================================================
# Session state
# =============================================================================

def fresh_context():
    return AssistantContext(ConversationManager())


def init_state():
    chat_store.init_db()
    defaults = {
        "context": None,
        "messages": [],
        "chat_id": None,          # None until the chat has something worth saving
        "chat_title": "New chat",
        "pending_prompt": None,
        "csv_signature": None,
        "uploader_key": 0,
        "flash": None,            # one-off message shown after a rerun
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if st.session_state.context is None:
        st.session_state.context = fresh_context()


def ctx():
    return st.session_state.context


# =============================================================================
# Saving and loading chats
# =============================================================================

def persist(save_datasets=False):
    """Save the current chat (creating it on first save)."""
    state = st.session_state
    if not state.messages:
        return
    if state.chat_id is None:
        state.chat_id = chat_store.new_chat_id()
        first_user = next((m["content"] for m in state.messages if m["role"] == "user"), None)
        if first_user:
            state.chat_title = make_chat_title(first_user)
        elif ctx().has_csv:
            state.chat_title = make_chat_title("Data: " + ", ".join(ctx().csv_data["dataframes"]))
        save_datasets = True
    elif state.chat_title in ("New chat", "Schema setup") or state.chat_title.startswith("Data: "):
        # Upgrade a placeholder title once the user asks a real question.
        questions = [m["content"] for m in state.messages if m["role"] == "user"]
        real = [q for q in questions if "create table" not in q.lower()]
        if real:
            state.chat_title = make_chat_title(real[0])

    chat_store.save_chat(
        state.chat_id, state.chat_title, ctx().to_memory(), state.messages,
        csv_data=ctx().csv_data, save_datasets=save_datasets,
    )


def start_new_chat():
    state = st.session_state
    state.context = fresh_context()
    state.messages = []
    state.chat_id = None
    state.chat_title = "New chat"
    state.csv_signature = None
    state.uploader_key += 1


def open_chat(chat_id):
    saved = chat_store.load_chat(chat_id)
    if saved is None:
        st.session_state.flash = "That chat no longer exists."
        return
    state = st.session_state
    state.context = AssistantContext.from_memory(saved["memory"], saved["csv_data"])
    state.messages = saved["messages"]
    state.chat_id = saved["id"]
    state.chat_title = saved["title"]
    state.csv_signature = None
    state.uploader_key += 1


def rename_current_chat(new_title):
    if st.session_state.chat_id:
        chat_store.rename_chat(st.session_state.chat_id, new_title)
        st.session_state.chat_title = (new_title or "").strip()[:80] or "Untitled chat"


def delete_current_chat():
    if st.session_state.chat_id:
        chat_store.delete_chat(st.session_state.chat_id)
    start_new_chat()
    st.session_state.flash = "Chat deleted."


# =============================================================================
# Data actions
# =============================================================================

def announce_csv(prefix):
    data = ctx().csv_data
    names = ", ".join(f"`{name}`" for name in data["dataframes"])
    rows = sum(len(df) for df in data["dataframes"].values())
    st.session_state.messages.append({
        "role": "assistant",
        "result": {
            "kind": "schema",
            "text": f"{prefix} {names} ({rows:,} rows in total). "
                    "Here's what I found. Ask me anything about it.",
            "schema": data["schema"],
        },
    })


def load_sample_data():
    files = sorted(SAMPLE_DIR.glob("*.csv"))
    try:
        ctx().csv_data = process_csv_files(files)
    except ValueError as error:
        st.session_state.flash = str(error)
        return
    ctx().sync_manager()
    announce_csv("Loaded the sample sales data:")
    persist(save_datasets=True)


def use_sample_schema():
    st.session_state.pending_prompt = SAMPLE_SCHEMA


def ask(question):
    st.session_state.pending_prompt = question


def remove_csv_data():
    ctx().csv_data = None
    ctx().sync_manager()
    st.session_state.csv_signature = None
    st.session_state.uploader_key += 1
    persist(save_datasets=True)


def handle_uploads(files):
    """Process uploaded CSVs only when the selection actually changes."""
    signature = tuple(sorted((f.name, f.size) for f in files)) if files else None
    if signature == st.session_state.csv_signature:
        return
    st.session_state.csv_signature = signature

    if not files:
        # The user removed the files from the uploader.
        if ctx().has_csv:
            ctx().csv_data = None
            ctx().sync_manager()
            persist(save_datasets=True)
        return

    try:
        ctx().csv_data = process_csv_files(files)
    except ValueError as error:
        st.sidebar.error(str(error))
        return

    ctx().sync_manager()
    announce_csv("Loaded your data as")
    persist(save_datasets=True)


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div class="qp-brand">
            <div class="qp-logo">{ui.ICON_LOGO}</div>
            <div><div class="qp-brand-name">{APP_NAME}</div>
            <div class="qp-brand-sub">AI SQL assistant</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.button("New chat", icon=":material/add:", type="primary",
                  width="stretch", on_click=start_new_chat)

        render_chat_list()
        render_data_section()
        render_dialect_section()
        render_tables_section()

        st.markdown('<div class="qp-section">Help</div>', unsafe_allow_html=True)
        if st.button("How it works", icon=":material/help:", width="stretch"):
            ui.show_guide()

        if api_key_configured():
            status = f'<div class="qp-dot ok"></div>Gemini connected · {ui.esc(get_model())}'
        else:
            status = '<div class="qp-dot bad"></div>API key missing: see the .env file'
        st.markdown(f'<div class="qp-status" style="margin-top:.6rem">{status}</div>',
                    unsafe_allow_html=True)


def render_chat_list():
    chats = chat_store.list_chats(limit=MAX_SAVED_CHATS_SHOWN)
    st.markdown('<div class="qp-section">Recent chats</div>', unsafe_allow_html=True)
    if not chats:
        st.caption("Your chats will appear here, saved automatically.")
        return
    with st.container(height=min(46 * len(chats) + 10, 280), border=False, key="chat_list"):
        for chat in chats:
            active = chat["id"] == st.session_state.chat_id
            st.button(
                chat["title"],
                key=f"chat_{chat['id']}",
                icon=":material/chat_bubble:" if active else ":material/chat_bubble_outline:",
                type="secondary" if active else "tertiary",
                width="stretch",
                help=f"Last active {time_ago(chat['updated_at'])}",
                on_click=open_chat, args=(chat["id"],),
            )


def render_data_section():
    st.markdown('<div class="qp-section">Upload data</div>', unsafe_allow_html=True)
    files = st.file_uploader(
        "CSV files", type=["csv"], accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed",
    )
    st.caption("Each CSV becomes a table. A new upload replaces this chat's CSV data.")
    handle_uploads(files)


def render_dialect_section():
    st.markdown('<div class="qp-section">SQL dialect</div>', unsafe_allow_html=True)
    if ctx().has_csv:
        st.selectbox("Dialect", ["SQLite"], disabled=True, label_visibility="collapsed",
                     help="CSV data runs on SQLite, so queries are written for SQLite.")
        return
    labels = list(DIALECTS)
    current = next((label for label, value in DIALECTS.items() if value == ctx().dialect), "SQLite")
    choice = st.selectbox("Dialect", labels, index=labels.index(current),
                          label_visibility="collapsed", key=f"dialect_{st.session_state.uploader_key}")
    if DIALECTS[choice] != ctx().dialect:
        ctx().dialect = DIALECTS[choice]
        ctx().sync_manager()
        persist()


def render_tables_section():
    schema = ctx().combined_schema
    st.markdown('<div class="qp-section">Your tables</div>', unsafe_allow_html=True)
    if not schema:
        st.caption("No tables yet. Upload CSVs, or paste a schema into the chat.")
        return

    csv_tables = set(ctx().csv_data["dataframes"]) if ctx().has_csv else set()
    for table in schema["tables"]:
        if table["name"] in csv_tables:
            rows = len(ctx().csv_data["dataframes"][table["name"]])
            label = f"{table['name']} · {rows:,} rows"
            icon = ":material/table_chart:"
        else:
            label = f"{table['name']} · schema"
            icon = ":material/schema:"
        with st.expander(label, icon=icon):
            ui.render_schema_table(table)
            if table["name"] in csv_tables:
                original = ctx().csv_data["file_mapping"].get(table["name"], {}).get("original_filename")
                if original:
                    st.caption(f"From {original}")

    if csv_tables:
        st.button("Remove CSV data", icon=":material/delete_sweep:", width="stretch",
                  on_click=remove_csv_data)


# =============================================================================
# Main area
# =============================================================================

def render_landing():
    ui.render_hero()
    ui.render_steps()
    if not api_key_configured():
        ui.render_setup_warning()
    ui.render_path_cards(on_sample_schema=use_sample_schema, on_sample_data=load_sample_data)


def render_conversation():
    state = st.session_state
    ui.render_chat_header(state.chat_title, ctx(), rename_current_chat,
                          delete_current_chat, state.chat_id)
    st.write("")

    for index, message in enumerate(state.messages):
        if message["role"] == "user":
            with st.chat_message("user", avatar=":material/person:"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar=":material/auto_awesome:"):
                ui.render_result(message["result"], key=f"{state.chat_id}_{index}")

    # Suggest questions until the user has asked one.
    has_question = any(
        m["role"] == "user" and "create table" not in m["content"].lower()
        for m in state.messages
    )
    if state.messages and not has_question and ctx().combined_schema:
        sample_loaded = ctx().has_csv and set(ctx().csv_data["dataframes"]) == {"customers", "orders", "products"}
        questions = SAMPLE_DATA_QUESTIONS if sample_loaded else SCHEMA_QUESTIONS
        if ctx().has_csv and not sample_loaded:
            first = next(iter(ctx().csv_data["dataframes"]))
            questions = [f"Show the first 10 rows of {first}",
                         f"How many rows are in {first}?",
                         "Summarise the numeric columns"]
        ui.render_suggestions(questions, on_pick=ask, key_prefix=f"sugg_{state.chat_id}")


def process_prompt(prompt):
    state = st.session_state
    state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=":material/auto_awesome:"):
        with st.spinner("Thinking…"):
            result = handle_message(prompt, ctx())
        ui.render_result(result, key=f"live_{len(state.messages)}")

    state.messages.append({"role": "assistant", "result": result})
    persist()


def main():
    init_state()
    inject_css()
    render_sidebar()

    if st.session_state.flash:
        st.toast(st.session_state.flash)
        st.session_state.flash = None

    if st.session_state.messages or st.session_state.pending_prompt:
        render_conversation()
    else:
        render_landing()

    typed = st.chat_input("Ask a question, paste a schema, or paste an SQL error…")
    prompt = typed or st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    if prompt and prompt.strip():
        process_prompt(prompt.strip())
        st.rerun()


main()
