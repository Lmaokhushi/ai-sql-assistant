"""
Saves chats to a local SQLite file (storage/querypilot.db) so they survive
closing the browser or restarting the app.

Each chat stores:
- its messages (what you see on screen, including result tables)
- its memory: schema, dialect, conversation history and latest SQL
- any CSV data uploaded in that chat, so follow-up questions still run
"""

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import pandas as pd

from utils.helpers import deserialize_result, now_iso, serialize_result, to_json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "storage" / "querypilot.db"


def _db_path():
    # Tests point this somewhere temporary with QUERYPILOT_DB.
    return Path(os.getenv("QUERYPILOT_DB", DEFAULT_DB_PATH))


@contextmanager
def _connect():
    """Open the database, commit on success, roll back on error, always close."""
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with _connect() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS chats (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            memory_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS messages (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id      TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
            position     INTEGER NOT NULL,
            role         TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS datasets (
            chat_id      TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
            table_name   TEXT NOT NULL,
            csv_text     TEXT NOT NULL,
            mapping_json TEXT NOT NULL,
            PRIMARY KEY (chat_id, table_name)
        );
        CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, position);
        """)


def new_chat_id():
    return uuid.uuid4().hex[:12]


def list_chats(limit=50):
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, title, created_at, updated_at FROM chats "
            "ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def chat_exists(chat_id):
    with _connect() as connection:
        row = connection.execute("SELECT 1 FROM chats WHERE id = ?", (chat_id,)).fetchone()
    return row is not None


def save_chat(chat_id, title, memory, messages, csv_data=None, save_datasets=False):
    """
    Create or update a chat. Messages are rewritten each time (chats are small).
    Datasets are only rewritten when save_datasets=True (i.e. after an upload),
    because CSVs can be large.
    """
    timestamp = now_iso()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO chats (id, title, created_at, updated_at, memory_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                updated_at = excluded.updated_at,
                memory_json = excluded.memory_json
            """,
            (chat_id, title, timestamp, timestamp, to_json(memory)),
        )

        connection.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        connection.executemany(
            "INSERT INTO messages (chat_id, position, role, payload_json) VALUES (?, ?, ?, ?)",
            [
                (chat_id, i, m["role"], to_json(_message_payload(m)))
                for i, m in enumerate(messages)
            ],
        )

        if save_datasets:
            connection.execute("DELETE FROM datasets WHERE chat_id = ?", (chat_id,))
            if csv_data and csv_data.get("dataframes"):
                for table_name, dataframe in csv_data["dataframes"].items():
                    connection.execute(
                        "INSERT INTO datasets (chat_id, table_name, csv_text, mapping_json) "
                        "VALUES (?, ?, ?, ?)",
                        (
                            chat_id,
                            table_name,
                            dataframe.to_csv(index=False),
                            to_json(csv_data["file_mapping"].get(table_name, {})),
                        ),
                    )


def _message_payload(message):
    if message["role"] == "user":
        return {"content": message["content"]}
    return {"result": serialize_result(message["result"])}


def load_chat(chat_id):
    """
    Return {"id", "title", "memory", "messages", "csv_data"} or None.
    """
    with _connect() as connection:
        chat = connection.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
        if chat is None:
            return None
        message_rows = connection.execute(
            "SELECT role, payload_json FROM messages WHERE chat_id = ? ORDER BY position",
            (chat_id,),
        ).fetchall()
        dataset_rows = connection.execute(
            "SELECT table_name, csv_text, mapping_json FROM datasets WHERE chat_id = ?",
            (chat_id,),
        ).fetchall()

    messages = []
    for row in message_rows:
        payload = json.loads(row["payload_json"])
        if row["role"] == "user":
            messages.append({"role": "user", "content": payload["content"]})
        else:
            messages.append({"role": "assistant", "result": deserialize_result(payload["result"])})

    memory = json.loads(chat["memory_json"] or "{}")
    csv_data = _rebuild_csv_data(dataset_rows, memory.get("csv_schema"))

    return {
        "id": chat["id"],
        "title": chat["title"],
        "memory": memory,
        "messages": messages,
        "csv_data": csv_data,
    }


def _rebuild_csv_data(rows, csv_schema):
    if not rows or not csv_schema:
        return None
    dataframes = {}
    file_mapping = {}
    for row in rows:
        dataframes[row["table_name"]] = pd.read_csv(StringIO(row["csv_text"]))
        file_mapping[row["table_name"]] = json.loads(row["mapping_json"])
    return {"dataframes": dataframes, "schema": csv_schema, "file_mapping": file_mapping}


def rename_chat(chat_id, title):
    title = (title or "").strip()[:80] or "Untitled chat"
    with _connect() as connection:
        connection.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))


def delete_chat(chat_id):
    with _connect() as connection:
        connection.execute("DELETE FROM chats WHERE id = ?", (chat_id,))


def delete_all_chats():
    with _connect() as connection:
        connection.execute("DELETE FROM chats")
