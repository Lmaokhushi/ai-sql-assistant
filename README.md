# QueryPilot: AI-Powered SQL Assistant

Ask questions about your data in plain English and get SQL you can trust.
Upload CSV files to see real answers, or describe your own database to get
SQL written for MySQL, PostgreSQL, BigQuery, Snowflake, SQL Server or SQLite.

---

## 1. Setup (about 5 minutes)

You need **Python 3.10 or newer**. Check with `python3 --version`.

Open **Terminal**, go into the project folder, and run:

```bash
cd path/to/ai-sql-assistant

# 1. Create a private Python environment for this project (one time only)
python3 -m venv venv

# 2. Turn it on (do this every time you open a new Terminal)
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install the packages
pip install -r requirements.txt
```

### Add your Gemini API key

1. Get a free key at <https://aistudio.google.com/apikey>.
2. Open the file called **`.env`** in the project folder.
   > On a Mac, files starting with a dot are hidden in Finder. Press
   > **Cmd + Shift + .** to show them, or open the folder in VS Code.
3. Replace `paste-your-gemini-api-key-here` with your key:
   ```
   GEMINI_API_KEY=AIzaSy...your-key...
   ```
4. Save the file. (`.gitignore` already stops this file from being uploaded to GitHub.)

### Run the app

```bash
streamlit run app.py
```

Your browser opens at <http://localhost:8501>. The sidebar status should say
**Gemini connected** with a green dot.

---

## 2. How to use it

| You want to… | Do this |
|---|---|
| Try it instantly | Click **Try sample sales data** on the home page |
| Query your spreadsheets | Upload CSV files in the sidebar under **Upload data** |
| Get SQL for your own database | Paste your `CREATE TABLE` statements into the chat, or describe your tables in plain English |
| Change the query | Just say it: *"only 2025"*, *"sort by city"*, *"use a LEFT JOIN"* |
| Fix an error | Paste the error message from your database into the chat |
| Understand a query | Ask *"explain this query"* |
| Come back later | Open it from **Recent chats** in the sidebar |
| Rename or delete a chat | Use the **⋯** button next to the chat title |

Click **How it works** in the sidebar at any time for the in-app guide.

The app follows your **light or dark** mode automatically. To switch it, use
**⋮ → Settings → Theme** in the top-right corner.

---

## 3. How it works (under the hood)

```
You type a message
      │
      ▼
ai_engine/orchestrator.py ── decides what the message is:
      │
      ├─ a schema (CREATE TABLE / description) → schema/schema_parser.py
      ├─ a new question  → ai_engine/sql_generator.py   (Gemini writes SQL)
      ├─ a follow-up     → ai_engine/sql_refiner.py     (Gemini edits the SQL)
      └─ an error report → ai_engine/sql_refiner.py     (Gemini diagnoses + fixes)
      │
      ▼
validation/sql_validator.py ── checks the SQL: one read-only SELECT, real tables
      │                        and columns. If it fails, Gemini gets one
      │                        automatic attempt to fix it.
      ▼
data/query_executor.py ─────── if CSVs are loaded: runs the SQL in a temporary,
      │                        read-only, in-memory SQLite database
      ▼
utils/chat_store.py ────────── saves the chat, its memory and its data
```

### Memory

Each chat has its own memory, managed by `utils/conversation_manager.py`:
the schema, the dialect, the conversation history and the latest SQL.
That history goes to Gemini with every request, which is why follow-ups like
*"what about last year?"* work.

Chats are saved to `storage/querypilot.db`, a SQLite file on your computer, after
every message. Uploaded CSV data is saved with the chat, so reopening a chat
lets you keep querying the same data without uploading it again.

---

## 4. Project structure

```
ai-sql-assistant/
├── app.py                     # The Streamlit app: layout, sidebar, chat, saving
├── config.py                  # App name, colours (light + dark), examples
├── .env                       # Your API key (private)
├── .env.example               # Template of .env without a real key
├── requirements.txt
├── .streamlit/config.toml     # Light and dark Streamlit themes
│
├── ai_engine/
│   ├── gemini_client.py       # The only file that talks to Gemini
│   ├── sql_generator.py       # Question → SQL
│   ├── sql_refiner.py         # Refine SQL / diagnose errors
│   └── orchestrator.py        # Routes each chat message
│
├── schema/
│   ├── schema_processor.py    # Validates and formats schemas
│   └── schema_parser.py       # CREATE TABLE / plain English → schema
│
├── validation/
│   └── sql_validator.py       # SQLGlot safety and correctness checks
│
├── data/
│   ├── csv_processor.py       # CSV files → tables + schema
│   └── query_executor.py      # Safe, read-only SQLite execution
│
├── utils/
│   ├── conversation_manager.py  # Per-chat memory
│   ├── chat_store.py            # Saves and loads chats
│   └── helpers.py
│
├── ui/
│   ├── styles.py              # All CSS (switches with light/dark)
│   └── components.py          # Landing page, guide, result display
│
├── sample_data/               # Demo CSVs: customers, orders, products
├── storage/                   # Saved chats appear here
└── tests/                     # 47 automated tests
```

---

## 5. Run the tests

```bash
python -m pytest -q
```

The tests replace Gemini with fake responses, so they run offline and don't use
any of your API quota.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| Red dot: **API key missing** | Check `.env` contains `GEMINI_API_KEY=your-key`, with no quotes or spaces. Save the file, then refresh the page. |
| "Gemini rejected the API key" | The key is wrong or was deleted. Make a new one at aistudio.google.com. |
| "doesn't recognise the model" | Change `GEMINI_MODEL` in `.env` to a model your key can use, for example `gemini-2.5-flash`. |
| `ModuleNotFoundError` | Turn on the environment (`source venv/bin/activate`), then run `pip install -r requirements.txt`. |
| Want to delete all saved chats | Stop the app and delete `storage/querypilot.db`. |

---

## 7. Before deploying publicly

This app is built to run on your own computer. Before putting it online:

- **Saved chats are shared by everyone using the same server.** There are no user
  accounts, so all visitors would see the same chat list. Add login (for example
  `st.login`) and store chats per user first.
- On Streamlit Community Cloud, put `GEMINI_API_KEY` in the app's **Secrets**
  instead of a `.env` file, and never commit `.env`.
- Uploaded CSVs are kept in the database. Consider a size limit and automatic
  clean-up.
- Every query goes through validation and a read-only SQLite authorizer, but
  generated SQL should still be reviewed before you run it on a real production
  database.
