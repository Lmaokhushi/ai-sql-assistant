"""
Branding and UI settings. Change the name, tagline or colours here
and the whole app follows.
"""

APP_NAME = "QueryPilot"
APP_TAGLINE = "Ask questions in plain English. Get SQL you can trust, and real answers from your data."
APP_ICON = "🧭"  # shown in the browser tab

# Two palettes. The app picks one to match the viewer's light or dark theme.
THEMES = {
    "light": {
        "background": "#F4F8FD",
        "background_glow": "rgba(40, 120, 200, 0.10)",
        "surface": "#FFFFFF",
        "surface_alt": "#F8FBFF",
        "text": "#173D64",
        "muted": "#71869D",
        "border": "#DFEAF6",
        "border_strong": "#B9D3EE",
        "tint": "#EAF4FF",
        "primary": "#2878C8",
        "primary_dark": "#1F63A8",
        "primary_text": "#2878C8",
        "accent": "#6C5CE7",
        "shadow": "rgba(23, 61, 100, 0.07)",
        "glow": "rgba(40, 120, 200, 0.28)",
        "success": "#1E8E5A",
        "success_bg": "#E8F6EF",
        "warning": "#A86A00",
        "warning_bg": "#FFF5E0",
        "danger": "#C0392B",
        "danger_bg": "#FDECEA",
    },
    "dark": {
        "background": "#0A1320",
        "background_glow": "rgba(40, 120, 200, 0.16)",
        "surface": "#111D2F",
        "surface_alt": "#0E1928",
        "text": "#E6EEF8",
        "muted": "#93A7BF",
        "border": "#213450",
        "border_strong": "#2F4C70",
        "tint": "#15273E",
        "primary": "#2F86DA",
        "primary_dark": "#1F63A8",
        "primary_text": "#74B4F2",
        "accent": "#9D8CFF",
        "shadow": "rgba(0, 0, 0, 0.35)",
        "glow": "rgba(47, 134, 218, 0.35)",
        "success": "#4CD08F",
        "success_bg": "rgba(76, 208, 143, 0.12)",
        "warning": "#F2B54B",
        "warning_bg": "rgba(242, 181, 75, 0.12)",
        "danger": "#FF8A80",
        "danger_bg": "rgba(255, 138, 128, 0.12)",
    },
}

DIALECTS = {
    "SQLite": "sqlite",
    "MySQL": "mysql",
    "PostgreSQL": "postgresql",
    "BigQuery": "bigquery",
    "Snowflake": "snowflake",
    "SQL Server (T-SQL)": "tsql",
}

SAMPLE_SCHEMA = """CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name TEXT,
    city TEXT,
    signup_date DATE
);
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    amount DECIMAL(10, 2),
    order_date DATE
);"""

# Suggested questions shown once data is available.
SCHEMA_QUESTIONS = [
    "Which 5 customers spent the most?",
    "Show total revenue by month",
    "How many new customers signed up each year?",
]
SAMPLE_DATA_QUESTIONS = [
    "Which 5 customers spent the most in total?",
    "Show revenue by product category",
    "How many orders were cancelled or returned each month?",
]

MAX_RESULT_ROWS = 1000
MAX_SAVED_CHATS_SHOWN = 30
