"""
End-to-end tests of the Streamlit app with Gemini mocked out.
"""
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TOP = ("SELECT c.name, SUM(o.quantity * p.unit_price) AS total_spent FROM customers c "
       "JOIN orders o ON c.customer_id = o.customer_id JOIN products p ON o.product_id = p.product_id "
       "GROUP BY c.name ORDER BY total_spent DESC LIMIT 5")


def start():
    return AppTest.from_file(APP, default_timeout=30).run()


def button(at, label):
    return next(b for b in at.button if b.label == label)


def test_landing_renders():
    at = start()
    assert not at.exception
    labels = [b.label for b in at.button]
    assert "Try sample sales data" in labels and "How it works" in labels


def test_sample_data_question_and_persistence():
    at = start()
    button(at, "Try sample sales data").click().run()
    assert not at.exception
    assert at.session_state.context.has_csv
    assert at.session_state.chat_id is not None  # saved straight away

    with mock.patch("ai_engine.orchestrator.generate_sql", return_value=TOP):
        at.chat_input[0].set_value("Which 5 customers spent the most?").run()
    assert not at.exception
    result = at.session_state.messages[-1]["result"]
    assert result["execution"]["success"] and result["execution"]["row_count"] == 5
    chat_id = at.session_state.chat_id

    # A brand-new browser session (like restarting the app) sees the saved chat...
    at2 = start()
    chat_button = next(b for b in at2.button if b.key == f"chat_{chat_id}")
    chat_button.click().run()
    assert not at2.exception
    assert at2.session_state.chat_title.startswith("Which 5 customers")
    assert len(at2.session_state.messages) == 3
    # ...with its data and memory, so follow-ups still run.
    assert at2.session_state.context.has_csv
    assert at2.session_state.context.manager.get_latest_sql() == TOP
    with mock.patch("ai_engine.orchestrator.refine_sql", return_value={
        "success": True, "diagnosis": "You want only the top 3.", "explanation": "Changed LIMIT to 3.",
        "corrected_sql": TOP.replace("LIMIT 5", "LIMIT 3"),
        "validation": {"valid": True, "errors": [], "sql": ""}, "message": ""}):
        at2.chat_input[0].set_value("now only show the top 3").run()
    assert at2.session_state.messages[-1]["result"]["execution"]["row_count"] == 3


def test_schema_example_and_delete():
    at = start()
    button(at, "Try a sample schema").click().run()
    assert not at.exception
    assert at.session_state.context.user_schema is not None
    chat_id = at.session_state.chat_id
    assert chat_id

    button(at, "Delete chat").click().run()
    assert not at.exception
    assert at.session_state.chat_id is None
    from utils import chat_store
    assert chat_store.load_chat(chat_id) is None


def test_guide_and_new_chat():
    at = start()
    button(at, "How it works").click().run()
    assert not at.exception
    button(at, "New chat").click().run()
    assert not at.exception and at.session_state.messages == []


def test_dialect_change_persists_in_memory():
    at = start()
    button(at, "Try a sample schema").click().run()
    at.selectbox[0].set_value("PostgreSQL").run()
    assert not at.exception
    assert at.session_state.context.active_dialect == "postgresql"
