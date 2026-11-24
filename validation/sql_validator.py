import sqlglot
from sqlglot import exp


# Supported SQL dialects and their SQLGlot names.
SUPPORTED_DIALECTS = {
    "sqlite": "sqlite",
    "mysql": "mysql",
    "postgresql": "postgres",
    "postgres": "postgres",
    "bigquery": "bigquery",
    "snowflake": "snowflake",
    "tsql": "tsql"
}


def normalize_dialect(dialect):
    """
    Check the requested SQL dialect and return
    the corresponding SQLGlot dialect name.
    """

    if not isinstance(dialect, str):
        raise ValueError("SQL dialect must be a string.")

    normalized = dialect.strip().lower()

    if normalized not in SUPPORTED_DIALECTS:
        raise ValueError(
            f"Unsupported SQL dialect: {dialect}"
        )

    return SUPPORTED_DIALECTS[normalized]


def build_schema_lookup(schema):
    """
    Create dictionaries that make it easier to find
    tables and columns in the user's database schema.
    """

    tables = {}

    for table in schema["tables"]:

        table_name = table["name"].strip().lower()

        columns = {
            column["name"].strip().lower()
            for column in table["columns"]
        }

        tables[table_name] = columns

    return tables


def check_statement_type(statement):
    """
    Allow only read-only query statements.

    Reject INSERT, UPDATE, DELETE, DROP, ALTER,
    CREATE and other modification operations.
    """

    if not isinstance(statement, exp.Query):
        return False

    forbidden_names = [
        "Insert",
        "Update",
        "Delete",
        "Create",
        "Drop",
        "Alter",
        "Merge",
        "Command",
        "TruncateTable"
    ]

    forbidden_types = tuple(
        getattr(exp, name)
        for name in forbidden_names
        if hasattr(exp, name)
    )

    for node in statement.walk():

        if isinstance(node, forbidden_types):
            return False

    return True


def validate_table_and_column_names(statement, schema):
    """
    Check whether referenced tables and columns
    exist in the supplied database schema.

    Handles ordinary table aliases and basic CTE references.
    """

    errors = []

    schema_tables = build_schema_lookup(schema)

    # Collect CTE names.
    cte_names = {
        cte.alias_or_name.lower()
        for cte in statement.find_all(exp.CTE)
    }

    # Collect aliases for physical tables.
    alias_to_table = {}
    referenced_tables = set()

    for table in statement.find_all(exp.Table):

        table_name = table.name.lower()

        # CTE names are not physical database tables.
        if table_name in cte_names:
            continue

        if table_name not in schema_tables:
            errors.append(
                f"Unknown table: '{table.name}'"
            )
            continue

        referenced_tables.add(table_name)

        alias = table.alias_or_name.lower()
        alias_to_table[alias] = table_name

    # Collect aliases for derived tables and subqueries.
    derived_aliases = {
        subquery.alias_or_name.lower()
        for subquery in statement.find_all(exp.Subquery)
        if subquery.alias
    }

    # Collect output aliases such as "SUM(amount) AS total", which
    # may be reused in ORDER BY / GROUP BY / HAVING.
    select_aliases = {
        alias.alias.lower()
        for alias in statement.find_all(exp.Alias)
        if alias.alias
    }

    # Validate column references.
    for column in statement.find_all(exp.Column):

        column_name = column.name.lower()

        # Ignore wildcard references such as SELECT *.
        if column_name == "*":
            continue

        # Unqualified references to a SELECT alias are valid.
        if not column.table and column_name in select_aliases:
            continue

        qualifier = column.table.lower()

        if qualifier:

            # The column belongs to a physical table alias.
            if qualifier in alias_to_table:

                actual_table = alias_to_table[qualifier]

                if column_name not in schema_tables[actual_table]:
                    errors.append(
                        f"Unknown column '{column.name}' "
                        f"in table '{actual_table}'."
                    )

            # CTE and derived-table columns require
            # additional scope-aware validation.
            elif qualifier in cte_names or qualifier in derived_aliases:
                continue

            else:
                errors.append(
                    f"Unknown table or alias '{column.table}' "
                    f"used with column '{column.name}'."
                )

        else:

            # Find all referenced physical tables containing
            # this unqualified column.
            matching_tables = [
                table_name
                for table_name in referenced_tables
                if column_name in schema_tables[table_name]
            ]

            if len(matching_tables) == 0:
                errors.append(
                    f"Unknown column: '{column.name}'."
                )

            elif len(matching_tables) > 1:
                errors.append(
                    f"Ambiguous column: '{column.name}'. "
                    "Qualify it with a table name or alias."
                )

    return errors


def validate_sql(sql, schema, dialect="sqlite"):
    """
    Main SQL validation function.

    Returns a dictionary containing:
    - valid: True or False
    - errors: List of validation errors
    - sql: Original SQL query
    """

    errors = []

    # Check that SQL is provided.
    if not isinstance(sql, str) or not sql.strip():
        return {
            "valid": False,
            "errors": ["SQL query cannot be empty."],
            "sql": sql
        }

    # Validate the supplied database schema.
    from schema.schema_processor import validate_schema

    schema_errors = validate_schema(schema)

    if schema_errors:
        return {
            "valid": False,
            "errors": [
                "Invalid database schema: " + error
                for error in schema_errors
            ],
            "sql": sql
        }

    # Normalize the SQL dialect.
    try:
        normalized_dialect = normalize_dialect(dialect)

    except ValueError as error:
        return {
            "valid": False,
            "errors": [str(error)],
            "sql": sql
        }

    # Parse the SQL.
    try:
        statements = sqlglot.parse(
            sql,
            read=normalized_dialect
        )

    except sqlglot.errors.ParseError as error:
        return {
            "valid": False,
            "errors": [
                f"SQL syntax error: {error}"
            ],
            "sql": sql
        }

    # Remove empty statements.
    statements = [
        statement
        for statement in statements
        if statement is not None
    ]

    # Ensure exactly one statement exists.
    if len(statements) != 1:
        return {
            "valid": False,
            "errors": [
                "Exactly one SQL statement is allowed."
            ],
            "sql": sql
        }

    statement = statements[0]

    # Reject non-query and modification statements.
    if not check_statement_type(statement):
        return {
            "valid": False,
            "errors": [
                "Only read-only SELECT queries and "
                "SELECT-based CTE queries are allowed."
            ],
            "sql": sql
        }

    # Validate tables and columns.
    errors.extend(
        validate_table_and_column_names(
            statement,
            schema
        )
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "sql": sql
    }

