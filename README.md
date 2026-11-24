# 🧭 QueryPilot: AI-Powered SQL Assistant

Ask questions about your data in plain English and get SQL you can trust.

**Live demo:** https://your-app.streamlit.app

## Features
- **Chat with your data:** upload CSV files and get real answers, not just SQL
- **Bring your own database:** paste `CREATE TABLE` statements or describe your tables, and get SQL for MySQL, PostgreSQL, BigQuery, Snowflake, SQL Server or SQLite
- **Safe by design:** every query is checked with SQLGlot (one read-only `SELECT`, real tables and columns only) and runs in a read-only, in-memory SQLite sandbox with a time limit
- **Conversational:** refine queries ("only 2025", "sort by city"), paste errors to get fixes, or ask "explain this query"
- **Self-correcting:** if a generated query fails validation or execution, Gemini gets one automatic attempt to fix it
- **Saved chats with memory:** every chat keeps its schema, data and conversation
- **Light and dark mode**

## Tech stack
Python · Streamlit · Google Gemini (`google-genai`) · pandas · SQLite · SQLGlot · pytest

## How it works
```
Question → Orchestrator → Gemini writes SQL → SQLGlot validates → (auto-repair) → SQLite runs it → results
```

## Project structure
```
ai_engine/   Gemini client, SQL generator and refiner, orchestrator
schema/      schema validation and parsing
validation/  SQLGlot safety checks
data/        CSV processing and sandboxed execution
utils/       conversation memory, chat storage
ui/          components and styles
tests/       pytest suite
```
