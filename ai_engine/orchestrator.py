"""
The "brain" between the chat UI and the backend modules.

app.py calls handle_message() with whatever the user typed. This module decides
what the message is (a schema, a new question, a follow-up or an error report),
calls the existing backend functions, and returns one result dictionary that
the UI knows how to display.

Nothing here talks to Streamlit, so it can be tested on its own.
"""

import re

import sqlglot

from ai_engine.sql_generator import CANNOT_GENERATE_PREFIX, generate_sql
from ai_engine.sql_refiner import diagnose_sql_error, refine_sql
from data.query_executor import execute_query
from schema.schema_parser import (
    looks_like_create_table,
    looks_like_schema_description,
    merge_schemas,
    parse_schema_text,
)
from validation.sql_validator import validate_sql


# Words that suggest the user is changing the previous query
# rather than asking something brand new.
FOLLOW_UP_PATTERNS = [
    r"^(also|now|instead|then|and|but|only|just|actually)\b",
    r"\b(previous|last|that|this|the) (query|sql|result)",
    r"\b(change|modify|update|adjust|tweak|edit|fix|refine|rewrite|correct)\b",
    r"\b(add|remove|drop|include|exclude) (a |an |the )?(column|filter|limit|join|condition|where|order|sort|group)",
    r"\b(sort|order) (it|them|by)\b",
    r"\b(try again|didn'?t work|doesn'?t work|not working|wrong|incorrect)\b",
    r"\buse (a |an )?(join|subquery|cte|left join|inner join)\b",
    r"\b(explain|what does) (this|that|the|it)\b",
    r"\bwhy (is|does|did)\b",
]

ERROR_PATTERNS = [
    r"\berror\b",
    r"no such (table|column)",
    r"syntax error",
    r"near \"",
    r"\bambiguous column\b",
    r"\bunknown column\b",
    r"\bdoes not exist\b",
    r"\bORA-\d+",
    r"\bSQLSTATE\b",
]


class AssistantContext:
    """
    Everything the orchestrator needs to know about the current conversation.
    app.py keeps one of these in st.session_state.
    """

    def __init__(self, manager):
        self.manager = manager          # your existing ConversationManager
        self.user_schema = None         # schema typed or pasted by the user
        self.csv_data = None            # result of process_csv_files()
        self.dialect = "sqlite"         # dialect chosen in the sidebar

    # --- derived information -------------------------------------------------

    @property
    def has_csv(self):
        return bool(self.csv_data and self.csv_data.get("dataframes"))

    @property
    def csv_schema(self):
        return self.csv_data["schema"] if self.has_csv else None

    @property
    def combined_schema(self):
        return merge_schemas(self.user_schema, self.csv_schema)

    @property
    def active_dialect(self):
        # CSV data runs on SQLite, so SQL must be written for SQLite.
        return "sqlite" if self.has_csv else self.dialect

    def sync_manager(self):
        """Keep ConversationManager's schema and dialect in step."""
        self.manager.schema = self.combined_schema
        self.manager.dialect = self.active_dialect

    # --- saving and restoring (the chat's "memory") ------------------------

    def to_memory(self):
        """Everything needed to continue this chat later, as plain JSON data."""
        return {
            "manager": self.manager.to_dict(),
            "user_schema": self.user_schema,
            "csv_schema": self.csv_schema,
            "dialect": self.dialect,
        }

    @classmethod
    def from_memory(cls, memory, csv_data=None):
        from utils.conversation_manager import ConversationManager

        memory = memory or {}
        context = cls(ConversationManager.from_dict(memory.get("manager")))
        context.user_schema = memory.get("user_schema")
        context.dialect = memory.get("dialect") or "sqlite"
        context.csv_data = csv_data
        context.sync_manager()
        return context


# -----------------------------------------------------------------------------
# Message classification
# -----------------------------------------------------------------------------

def _matches_any(patterns, text):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify_message(message, context):
    """
    Return one of: "schema", "need_schema", "error", "refine", "generate".
    """
    text = message.strip()

    if looks_like_create_table(text):
        return "schema"

    if looks_like_schema_description(text) and not text.endswith("?"):
        return "schema"

    if context.combined_schema is None:
        return "need_schema"

    has_previous_sql = bool(context.manager.get_latest_sql())

    if has_previous_sql and _matches_any(ERROR_PATTERNS, text):
        return "error"

    if has_previous_sql and _matches_any(FOLLOW_UP_PATTERNS, text):
        return "refine"

    return "generate"


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def handle_message(message, context):
    """
    Process one chat message and return a result dictionary:

        {
            "kind": "schema" | "sql" | "info" | "error",
            "text": "Message to show above everything else",
            "sql": "SELECT ..." or None,
            "validation": {...} or None,
            "execution": {...} or None,
            "diagnosis": str or None,
            "explanation": str or None,
            "schema": {...} or None,
        }
    """
    route = classify_message(message, context)

    try:
        if route == "schema":
            result = _handle_schema(message, context)
        elif route == "need_schema":
            result = _info(
                "I need to know what your data looks like first. Paste your "
                "`CREATE TABLE` statements, describe your tables in plain English, "
                "or upload CSV files with the uploader below the chat."
            )
        elif route in ("refine", "error"):
            result = _handle_refinement(message, context, is_error=(route == "error"))
        else:
            result = _handle_generation(message, context)

    except (ValueError, RuntimeError) as error:
        result = _error(str(error))
    except Exception as error:  # last-resort safety net so the UI never crashes
        result = _error(f"Something unexpected went wrong: {error}")

    _record(context, message, result)
    return result


# -----------------------------------------------------------------------------
# Route handlers
# -----------------------------------------------------------------------------

def _handle_schema(message, context):
    schema, errors = parse_schema_text(message)

    if errors:
        return _error(
            "I couldn't use that schema yet:\n\n" + "\n".join(f"- {e}" for e in errors)
        )

    context.user_schema = merge_schemas(context.user_schema, schema)
    context.sync_manager()

    table_names = ", ".join(f"`{t['name']}`" for t in schema["tables"])
    return {
        **_empty(),
        "kind": "schema",
        "text": f"Got it. I've saved {len(schema['tables'])} table(s): {table_names}. "
                "Ask me a question about this data.",
        "schema": schema,
    }


def _handle_generation(question, context):
    schema = context.combined_schema
    dialect = context.active_dialect

    context.manager.set_original_question(question)
    history = context.manager.get_recent_history(limit=8)
    sql = generate_sql(schema, question, dialect, conversation_history=history)

    if sql.startswith(CANNOT_GENERATE_PREFIX):
        reason = sql[len(CANNOT_GENERATE_PREFIX):].strip()
        return _info(
            f"I can't answer that with the current tables. {reason}"
        )

    validation = validate_sql(sql, schema, dialect)
    explanation = None

    # One automatic repair attempt if the first draft fails validation.
    if not validation["valid"]:
        repaired = _try_repair(
            context, sql,
            "The query failed validation: " + "; ".join(validation["errors"]),
        )
        if repaired:
            sql, validation = repaired["corrected_sql"], repaired["validation"]
            explanation = "I corrected my first draft: " + repaired["explanation"]

    return _finish_sql(context, sql, validation, explanation=explanation)


def _handle_refinement(message, context, is_error):
    schema = context.combined_schema
    dialect = context.active_dialect
    previous_sql = context.manager.get_latest_sql()
    history = context.manager.get_recent_history(limit=10)

    function = diagnose_sql_error if is_error else refine_sql
    kwargs = dict(
        schema=schema,
        previous_sql=previous_sql,
        sql_dialect=dialect,
        conversation_history=history,
    )
    if is_error:
        kwargs["error_message"] = message
    else:
        kwargs["user_message"] = message

    outcome = function(**kwargs)

    if not outcome["corrected_sql"]:
        return {
            **_empty(),
            "kind": "info",
            "text": outcome["message"],
            "diagnosis": outcome["diagnosis"],
            "explanation": outcome["explanation"],
        }

    return _finish_sql(
        context,
        outcome["corrected_sql"],
        outcome["validation"],
        diagnosis=outcome["diagnosis"],
        explanation=outcome["explanation"],
    )


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _finish_sql(context, sql, validation, diagnosis=None, explanation=None):
    """Save the SQL, run it on CSV data when possible, and build the result."""
    context.manager.set_latest_sql(sql)

    execution = None
    if validation["valid"] and context.has_csv:
        execution = _execute_on_csv(context, sql)

        # One automatic repair if SQLite rejects the query at run time.
        if execution and not execution["success"] and execution.get("validation", {}).get("valid"):
            repaired = _try_repair(context, sql, f"SQLite error: {execution['error']}")
            if repaired:
                sql, validation = repaired["corrected_sql"], repaired["validation"]
                context.manager.set_latest_sql(sql)
                explanation = "The first version failed when run, so I fixed it: " + repaired["explanation"]
                execution = _execute_on_csv(context, sql)

    if not validation["valid"]:
        text = "Here's a draft, but it didn't pass validation. Check the issues below, or tell me what to change."
    elif execution and execution["success"]:
        text = f"Here's your query. It returned **{execution['row_count']}** row(s)."
    elif execution and execution.get("skipped"):
        text = "Here's your query. " + execution["error"]
    elif execution:
        text = "Here's your query, but it failed when run on your data."
    else:
        text = "Here's your query. It passed validation. (It isn't run, because there's no uploaded data for these tables.)"

    return {
        **_empty(),
        "kind": "sql",
        "text": text,
        "sql": pretty_sql(sql, context.active_dialect),
        "validation": validation,
        "execution": execution,
        "diagnosis": diagnosis,
        "explanation": explanation,
    }


def pretty_sql(sql, dialect):
    """Lay SQL out over several lines for reading. Falls back to the original."""
    try:
        from validation.sql_validator import normalize_dialect
        name = normalize_dialect(dialect)
        formatted = sqlglot.transpile(sql, read=name, write=name, pretty=True)
        return formatted[0] if len(formatted) == 1 else sql
    except Exception:
        return sql


def _execute_on_csv(context, sql):
    """
    Run SQL on the uploaded CSVs. If the query uses tables that only exist in
    the typed schema, it can't run, so we say so instead of failing.
    """
    csv_check = validate_sql(sql, context.csv_schema, "sqlite")
    if not csv_check["valid"]:
        return {
            "success": False,
            "skipped": True,
            "error": "It uses tables that aren't in your uploaded files, so it was validated but not run.",
            "dataframe": None,
        }

    return execute_query(
        sql,
        context.csv_data["dataframes"],
        context.csv_schema,
    )


def _try_repair(context, sql, error_text):
    try:
        outcome = diagnose_sql_error(
            schema=context.combined_schema,
            previous_sql=sql,
            error_message=error_text,
            sql_dialect=context.active_dialect,
            conversation_history=context.manager.get_recent_history(limit=10),
        )
    except (ValueError, RuntimeError):
        return None

    if outcome.get("success") and outcome.get("corrected_sql"):
        return outcome
    return None


def _record(context, message, result):
    """Store both sides of the exchange in ConversationManager."""
    context.manager.add_message("user", message)

    summary = result["text"]
    if result.get("sql"):
        summary += f"\n\nSQL:\n{result['sql']}"
    context.manager.add_message("assistant", summary)


def _empty():
    return {
        "kind": "info", "text": "", "sql": None, "validation": None,
        "execution": None, "diagnosis": None, "explanation": None, "schema": None,
    }


def _info(text):
    return {**_empty(), "kind": "info", "text": text}


def _error(text):
    return {**_empty(), "kind": "error", "text": text}
