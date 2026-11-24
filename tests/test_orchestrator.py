from unittest import mock

from ai_engine import orchestrator as o
from utils.conversation_manager import ConversationManager

GOOD = ("SELECT c.name, SUM(o.order_amount) AS total FROM customers c "
        "JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name ORDER BY total DESC")


def make_context(csv_data=None):
    context = o.AssistantContext(ConversationManager())
    context.csv_data = csv_data
    context.sync_manager()
    return context


def test_needs_schema_first():
    assert "data looks like" in o.handle_message("top customers?", make_context())["text"]


def test_create_table_saved():
    context = make_context()
    result = o.handle_message("CREATE TABLE t (id INT PRIMARY KEY, name TEXT);", context)
    assert result["kind"] == "schema" and context.user_schema


def test_csv_question_runs(csv_data):
    context = make_context(csv_data)
    with mock.patch.object(o, "generate_sql", return_value=GOOD):
        result = o.handle_message("who spent most?", context)
    assert result["execution"]["success"]
    assert result["execution"]["dataframe"].iloc[0]["name"] == "Bob"
    assert context.manager.get_latest_sql() == GOOD
    assert len(context.manager.get_history()) == 2


def test_auto_repair(csv_data):
    context = make_context(csv_data)
    fixed = {"success": True, "corrected_sql": "SELECT name FROM customers",
             "validation": {"valid": True, "errors": []}, "explanation": "typo", "diagnosis": "x", "message": ""}
    with mock.patch.object(o, "generate_sql", return_value="SELECT nme FROM customers"), \
         mock.patch.object(o, "diagnose_sql_error", return_value=fixed):
        result = o.handle_message("list names", context)
    assert result["execution"]["row_count"] == 3


def test_routing(csv_data):
    context = make_context(csv_data)
    context.manager.set_latest_sql("SELECT name FROM customers")
    assert o.classify_message("now sort it by city", context) == "refine"
    assert o.classify_message("I got: no such column: nme", context) == "error"
    assert o.classify_message("how many orders are there?", context) == "generate"
    assert o.classify_message("explain this query", context) == "refine"


def test_cannot_generate(csv_data):
    context = make_context(csv_data)
    with mock.patch.object(o, "generate_sql", return_value="-- CANNOT_GENERATE: no weather data"):
        assert "can't answer" in o.handle_message("weather?", context)["text"]


def test_gemini_failure_is_friendly(csv_data):
    context = make_context(csv_data)
    with mock.patch.object(o, "generate_sql", side_effect=RuntimeError("Gemini rejected the API key.")):
        result = o.handle_message("anything", context)
    assert result["kind"] == "error" and "API key" in result["text"]


def test_memory_round_trip(csv_data):
    context = make_context(csv_data)
    context.dialect = "mysql"
    with mock.patch.object(o, "generate_sql", return_value=GOOD):
        o.handle_message("who spent most?", context)
    restored = o.AssistantContext.from_memory(context.to_memory(), csv_data)
    assert restored.manager.get_latest_sql() == GOOD
    assert restored.active_dialect == "sqlite"
    assert restored.dialect == "mysql"
