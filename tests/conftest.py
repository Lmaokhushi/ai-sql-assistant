import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CUSTOMERS = "customer_id,Name,City\n1,Ann,Paris\n2,Bob,Rome\n3,Cara,Paris\n"
ORDERS = "order_id,customer_id,Order Amount ($)\n1,1,50\n2,1,20\n3,2,99\n"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test gets its own empty chat database."""
    monkeypatch.setenv("QUERYPILOT_DB", str(tmp_path / "test.db"))
    yield


@pytest.fixture
def csv_files(tmp_path):
    (tmp_path / "customers.csv").write_text(CUSTOMERS)
    (tmp_path / "orders.csv").write_text(ORDERS)
    return [tmp_path / "customers.csv", tmp_path / "orders.csv"]


@pytest.fixture
def csv_data(csv_files):
    from data.csv_processor import process_csv_files
    return process_csv_files(csv_files)


@pytest.fixture
def shop_schema():
    return {"tables": [
        {"name": "customers", "columns": [
            {"name": "customer_id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT"},
            {"name": "city", "type": "TEXT"},
        ]},
        {"name": "orders", "columns": [
            {"name": "order_id", "type": "INTEGER", "primary_key": True},
            {"name": "customer_id", "type": "INTEGER",
             "foreign_key": {"table": "customers", "column": "customer_id"}},
            {"name": "amount", "type": "REAL"},
        ]},
    ]}
