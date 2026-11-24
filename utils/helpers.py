"""
Small helper functions shared across the app.
"""

import json
import re
from datetime import datetime, timezone

import pandas as pd


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_chat_title(text, max_length=42):
    """Turn the first user message into a short chat title."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text:
        return "New chat"
    if re.search(r"\bcreate\s+table\b", text, re.IGNORECASE):
        return "Schema setup"
    if len(text) > max_length:
        text = text[: max_length - 1].rsplit(" ", 1)[0] + "…"
    return text[0].upper() + text[1:]


def time_ago(iso_string):
    """'2026-11-24T10:00:00+00:00' -> '5 min ago'."""
    try:
        then = datetime.fromisoformat(iso_string)
    except (TypeError, ValueError):
        return ""
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    seconds = int((datetime.now(timezone.utc) - then).total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600} h ago"
    days = seconds // 86400
    return "yesterday" if days == 1 else f"{days} days ago"


# ---- DataFrame <-> JSON (for saving query results with a chat) -------------

def dataframe_to_payload(dataframe, max_rows=1000):
    if dataframe is None:
        return None
    trimmed = dataframe.head(max_rows)
    return json.loads(trimmed.to_json(orient="split", index=False, date_format="iso"))


def payload_to_dataframe(payload):
    if not payload:
        return None
    return pd.DataFrame(payload.get("data", []), columns=payload.get("columns", []))


def serialize_result(result):
    """Make an assistant result JSON-safe (replace the DataFrame)."""
    if not result:
        return result
    result = dict(result)
    execution = result.get("execution")
    if execution:
        execution = dict(execution)
        execution["dataframe"] = dataframe_to_payload(execution.get("dataframe"))
        execution["_serialized"] = True
        result["execution"] = execution
    return result


def deserialize_result(result):
    """Reverse of serialize_result()."""
    if not result:
        return result
    result = dict(result)
    execution = result.get("execution")
    if execution and execution.get("_serialized"):
        execution = dict(execution)
        execution["dataframe"] = payload_to_dataframe(execution.get("dataframe"))
        execution.pop("_serialized", None)
        result["execution"] = execution
    return result


def to_json(value):
    return json.dumps(value, default=str)
