from utils.conversation_manager import ConversationManager


def test_conversation_manager():
    manager = ConversationManager()

    manager.set_context(schema={"customers": ["customer_id", "name"],
                                "orders": ["order_id", "customer_id", "amount"]},
                        dialect="mysql")
    assert manager.dialect == "mysql"
    assert manager.schema is not None

    manager.set_original_question("Find the top 10 customers by revenue.")

    sql = """
    SELECT customer_id, SUM(amount) AS revenue
    FROM orders GROUP BY customer_id ORDER BY revenue DESC LIMIT 10;
    """
    manager.set_latest_sql(sql)
    assert manager.get_latest_sql() == sql.strip()

    manager.add_message("user", "Find the top 10 customers by revenue.")
    manager.add_message("assistant", "Here is your SQL query.")
    assert len(manager.get_history()) == 2

    recent = manager.get_recent_history(limit=1)
    assert len(recent) == 1 and recent[0]["role"] == "assistant"

    context = manager.get_context()
    assert context["dialect"] == "mysql"
    assert context["latest_sql"] == sql.strip()
    assert context["original_question"] is not None
    assert manager.has_context() is True

    manager.clear_history()
    assert len(manager.get_history()) == 0
    assert manager.schema is not None
    assert manager.latest_sql is None

    manager.reset()
    assert manager.schema is None
    assert manager.latest_sql is None
    assert manager.original_question is None
    assert len(manager.get_history()) == 0


def test_round_trip_keeps_memory():
    manager = ConversationManager()
    manager.set_context(schema={"tables": []}, dialect="postgresql")
    manager.add_message("user", "hi")
    manager.set_latest_sql("SELECT 1")
    restored = ConversationManager.from_dict(manager.to_dict())
    assert restored.get_history() == manager.get_history()
    assert restored.get_latest_sql() == "SELECT 1"
    assert restored.dialect == "postgresql"
