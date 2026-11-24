from unittest import mock

from ai_engine import orchestrator as o
from utils import chat_store
from utils.conversation_manager import ConversationManager
from tests.test_orchestrator import GOOD


def test_save_and_load_everything(csv_data):
    chat_store.init_db()
    context = o.AssistantContext(ConversationManager())
    context.csv_data = csv_data
    context.sync_manager()
    with mock.patch.object(o, "generate_sql", return_value=GOOD):
        result = o.handle_message("who spent most?", context)
    messages = [{"role": "user", "content": "who spent most?"}, {"role": "assistant", "result": result}]

    chat_store.save_chat("abc", "Spending", context.to_memory(), messages, csv_data, save_datasets=True)
    saved = chat_store.load_chat("abc")

    assert saved["title"] == "Spending"
    assert saved["messages"][1]["result"]["execution"]["dataframe"].iloc[0]["name"] == "Bob"
    assert set(saved["csv_data"]["dataframes"]) == {"customers", "orders"}

    restored = o.AssistantContext.from_memory(saved["memory"], saved["csv_data"])
    assert restored.manager.get_latest_sql() == GOOD
    # The restored chat can still run queries on its saved data.
    with mock.patch.object(o, "generate_sql", return_value="SELECT COUNT(*) AS n FROM orders"):
        again = o.handle_message("how many orders?", restored)
    assert again["execution"]["success"]


def test_list_rename_delete():
    chat_store.init_db()
    chat_store.save_chat("one", "First", {}, [{"role": "user", "content": "hi"}])
    chat_store.save_chat("two", "Second", {}, [{"role": "user", "content": "yo"}])
    assert len(chat_store.list_chats()) == 2
    chat_store.rename_chat("one", "Renamed")
    assert chat_store.load_chat("one")["title"] == "Renamed"
    chat_store.delete_chat("one")
    assert chat_store.load_chat("one") is None
    assert len(chat_store.list_chats()) == 1
