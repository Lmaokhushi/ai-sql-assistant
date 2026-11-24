import io

from data.csv_processor import normalize_identifier, process_csv_files
from data.query_executor import execute_query


def test_identifiers():
    assert normalize_identifier("Order Amount ($)") == "order_amount"
    assert normalize_identifier("2024 sales") == "column_2024_sales"


def test_process(csv_data):
    assert set(csv_data["dataframes"]) == {"customers", "orders"}
    cols = {c["name"]: c["type"] for c in csv_data["schema"]["tables"][1]["columns"]}
    assert cols == {"order_id": "INTEGER", "customer_id": "INTEGER", "order_amount": "INTEGER"}


def test_excel_style_csv():
    class Upload(io.BytesIO):
        name = "Sales Data.csv"
    data = process_csv_files([Upload("Café;Price\nx;1,5\n".encode("cp1252"))])
    assert "sales_data" in data["dataframes"]


def test_execute_join(csv_data):
    sql = ("SELECT c.name, SUM(o.order_amount) AS total FROM customers c "
           "JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name ORDER BY total DESC")
    result = execute_query(sql, csv_data["dataframes"], csv_data["schema"])
    assert result["success"], result
    assert result["dataframe"].iloc[0]["name"] == "Bob"


def test_execute_window_and_cte(csv_data):
    sql = ("WITH t AS (SELECT customer_id, order_amount, "
           "RANK() OVER (ORDER BY order_amount DESC) AS r FROM orders) SELECT t.customer_id FROM t WHERE t.r = 1")
    result = execute_query(sql, csv_data["dataframes"], csv_data["schema"])
    assert result["success"], result


def test_row_limit(csv_data):
    result = execute_query("SELECT name FROM customers", csv_data["dataframes"], csv_data["schema"], max_rows=2)
    assert result["row_count"] == 2 and result["truncated"]


def test_blocks_writes(csv_data):
    result = execute_query("DELETE FROM customers", csv_data["dataframes"], csv_data["schema"])
    assert not result["success"]
