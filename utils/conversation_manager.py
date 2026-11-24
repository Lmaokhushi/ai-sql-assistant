"""
Keeps track of one conversation: schema, dialect, message history,
the original question and the latest SQL.

to_dict() / from_dict() let the chat store save this "memory" to disk
and restore it when a saved chat is reopened.
"""

import copy


class ConversationManager:

    def __init__(self, max_history=50):
        self.max_history = max_history
        self.schema = None
        self.dialect = "sqlite"
        self.history = []
        self.original_question = None
        self.latest_sql = None

    # ---- context -----------------------------------------------------------

    def set_context(self, schema=None, dialect=None):
        """Set the schema and/or dialect. Passing None leaves a value unchanged."""
        if schema is not None:
            self.schema = copy.deepcopy(schema)
        if dialect is not None:
            self.dialect = dialect

    def has_context(self):
        return self.schema is not None

    def get_context(self):
        return {
            "schema": self.schema,
            "dialect": self.dialect,
            "original_question": self.original_question,
            "latest_sql": self.latest_sql,
            "history": self.get_history(),
        }

    # ---- messages ----------------------------------------------------------

    def add_message(self, role, content):
        if role not in ("user", "assistant", "system"):
            raise ValueError("role must be 'user', 'assistant' or 'system'.")
        self.history.append({"role": role, "content": str(content)})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_history(self):
        return list(self.history)

    def get_recent_history(self, limit=10):
        if limit <= 0:
            return []
        return self.history[-limit:]

    # ---- question and SQL --------------------------------------------------

    def set_original_question(self, question):
        self.original_question = question.strip() if isinstance(question, str) else question

    def set_latest_sql(self, sql):
        self.latest_sql = sql.strip() if isinstance(sql, str) else sql

    def get_latest_sql(self):
        return self.latest_sql

    # ---- clearing ----------------------------------------------------------

    def clear_history(self):
        """Forget the conversation but keep the schema and dialect."""
        self.history = []
        self.original_question = None
        self.latest_sql = None

    def reset(self):
        """Forget everything."""
        self.schema = None
        self.dialect = "sqlite"
        self.clear_history()

    # ---- saving and loading ------------------------------------------------

    def to_dict(self):
        return {
            "schema": self.schema,
            "dialect": self.dialect,
            "history": self.history,
            "original_question": self.original_question,
            "latest_sql": self.latest_sql,
        }

    @classmethod
    def from_dict(cls, data):
        manager = cls()
        data = data or {}
        manager.schema = data.get("schema")
        manager.dialect = data.get("dialect") or "sqlite"
        manager.history = list(data.get("history") or [])
        manager.original_question = data.get("original_question")
        manager.latest_sql = data.get("latest_sql")
        return manager
