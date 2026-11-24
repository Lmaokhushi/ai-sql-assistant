"""
One place for everything Gemini-related.

Every module that talks to Gemini calls ask_gemini() from here, so the API key,
model name and timeout are configured once, in the .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# The project folder (the one that contains app.py and .env).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_MODEL = "gemini-3.6-flash"
DEFAULT_TIMEOUT_MS = 60000

PLACEHOLDER_KEYS = {"", "paste-your-gemini-api-key-here", "your_api_key_here"}


def _load_env():
    # override=True means edits to .env are picked up without restarting.
    load_dotenv(ENV_FILE, override=True)


def get_model():
    _load_env()
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def get_timeout_ms():
    _load_env()
    try:
        return int(os.getenv("GEMINI_TIMEOUT_MS", DEFAULT_TIMEOUT_MS))
    except ValueError:
        return DEFAULT_TIMEOUT_MS


def get_api_key():
    """Return the API key, or None if it hasn't been set yet."""
    _load_env()
    key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    return None if key in PLACEHOLDER_KEYS else key


def api_key_configured():
    return get_api_key() is not None


class GeminiError(RuntimeError):
    """A Gemini problem explained in plain English."""


def _friendly_error(error):
    text = str(error)
    lowered = text.lower()

    if "api key not valid" in lowered or "api_key_invalid" in lowered or "permission_denied" in lowered:
        return "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file."
    if "429" in text or "resource_exhausted" in lowered or "quota" in lowered:
        return "Gemini's rate limit or quota was reached. Wait a minute and try again."
    if "404" in text or ("not found" in lowered and "model" in lowered):
        return (
            f"Gemini doesn't recognise the model '{get_model()}'. "
            "Change GEMINI_MODEL in your .env file."
        )
    if "timeout" in lowered or "timed out" in lowered or "deadline" in lowered:
        return "Gemini took too long to respond. Please try again."
    if "connect" in lowered or "network" in lowered or "resolve" in lowered:
        return "Couldn't reach Gemini. Check your internet connection."
    return f"Gemini request failed: {text}"


def ask_gemini(prompt):
    """
    Send a prompt to Gemini and return the response text.
    Raises GeminiError with a readable message if anything goes wrong.
    """
    api_key = get_api_key()
    if not api_key:
        raise GeminiError(
            "No Gemini API key found. Open the .env file in the project folder, "
            "paste your key after GEMINI_API_KEY=, save, and refresh the page."
        )

    from google import genai  # imported here so tests run without network setup

    client = genai.Client(
        api_key=api_key,
        http_options={"timeout": get_timeout_ms()},
    )
    try:
        response = client.models.generate_content(model=get_model(), contents=prompt)
        text = response.text
    except Exception as error:
        raise GeminiError(_friendly_error(error)) from error
    finally:
        if hasattr(client, "close"):
            client.close()

    if not text or not text.strip():
        raise GeminiError("Gemini returned an empty response. Please try again.")
    return text
