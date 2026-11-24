import pytest

from validation.sql_validator import normalize_dialect, validate_sql


def test_valid_join(shop_schema):
    sql = "SELECT c.name, SUM(o.amount) FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name"
    assert validate_sql(sql, shop_schema)["valid"]


def test_unknown_table(shop_schema):
    result = validate_sql("SELECT * FROM products", shop_schema)
    assert not result["valid"] and "Unknown table" in result["errors"][0]


def test_unknown_column(shop_schema):
    assert not validate_sql("SELECT nme FROM customers", shop_schema)["valid"]


def test_ambiguous_column(shop_schema):
    sql = "SELECT customer_id FROM customers JOIN orders ON customers.customer_id = orders.customer_id"
    result = validate_sql(sql, shop_schema)
    assert any("Ambiguous" in e for e in result["errors"])


@pytest.mark.parametrize("sql", [
    "DELETE FROM customers",
    "DROP TABLE customers",
    "UPDATE customers SET name = 'x'",
    "INSERT INTO customers VALUES (1, 'a', 'b')",
])
def test_rejects_modifications(sql, shop_schema):
    assert not validate_sql(sql, shop_schema)["valid"]


def test_single_statement_only(shop_schema):
    assert not validate_sql("SELECT name FROM customers; SELECT city FROM customers", shop_schema)["valid"]


def test_select_alias_in_order_by(shop_schema):
    sql = "SELECT customer_id, SUM(amount) AS total FROM orders GROUP BY customer_id ORDER BY total DESC"
    assert validate_sql(sql, shop_schema)["valid"]


def test_cte(shop_schema):
    sql = "WITH t AS (SELECT customer_id, SUM(amount) AS s FROM orders GROUP BY customer_id) SELECT t.s FROM t"
    assert validate_sql(sql, shop_schema)["valid"]


def test_empty_sql(shop_schema):
    assert not validate_sql("   ", shop_schema)["valid"]


def test_dialects():
    assert normalize_dialect("PostgreSQL") == "postgres"
    with pytest.raises(ValueError):
        normalize_dialect("oracle")


def test_unknown_alias(shop_schema):
    assert not validate_sql("SELECT z.name FROM customers", shop_schema)["valid"]
