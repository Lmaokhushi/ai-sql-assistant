from schema.schema_parser import looks_like_schema_description, merge_schemas, parse_create_table_sql
from schema.schema_processor import validate_schema


def test_create_table_with_keys():
    schema = parse_create_table_sql("""
        CREATE TABLE customers (customer_id INT PRIMARY KEY, name VARCHAR(100));
        CREATE TABLE orders (order_id INT, customer_id INT REFERENCES customers(customer_id),
                             PRIMARY KEY (order_id));
    """)
    assert validate_schema(schema) == []
    orders = schema["tables"][1]["columns"]
    assert orders[0]["primary_key"] is True
    assert orders[1]["foreign_key"] == {"table": "customers", "column": "customer_id"}


def test_detects_description():
    assert looks_like_schema_description("I have a users table with columns id and email")
    assert not looks_like_schema_description("Which users signed up today?")


def test_merge(shop_schema):
    extra = {"tables": [{"name": "products", "columns": [{"name": "id", "type": "INT"}]}]}
    assert len(merge_schemas(shop_schema, extra)["tables"]) == 3
