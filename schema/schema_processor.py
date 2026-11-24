
def validate_schema(schema):

    errors = []

    if not isinstance(schema, dict):
        return ["Schema must be a dictionary."]

    tables = schema.get("tables")

    if not isinstance(tables, list) or len(tables) == 0:
        return ["Schema must contain at least one table."]

    table_names = set()

    for table in tables:

        if not isinstance(table, dict):
            errors.append("Each table must be a dictionary.")
            continue

        table_name = table.get("name")

        if not isinstance(table_name, str) or not table_name.strip():
            errors.append("Every table must have a valid name.")
            continue

        normalized_table_name = table_name.strip().lower()

        if normalized_table_name in table_names:
            errors.append(
                f"Duplicate table name: {table_name}"
            )
            continue

        table_names.add(normalized_table_name)

        columns = table.get("columns")

        if not isinstance(columns, list) or len(columns) == 0:
            errors.append(
                f"Table '{table_name}' must have at least one column."
            )
            continue

        column_names = set()

        for column in columns:

            if not isinstance(column, dict):
                errors.append(
                    f"Invalid column definition in table '{table_name}'."
                )
                continue

            column_name = column.get("name")
            data_type = column.get("type")

            if not isinstance(column_name, str) or not column_name.strip():
                errors.append(
                    f"A column in table '{table_name}' has no valid name."
                )
                continue

            normalized_column_name = column_name.strip().lower()

            if normalized_column_name in column_names:
                errors.append(
                    f"Duplicate column '{column_name}' in table '{table_name}'."
                )
                continue

            column_names.add(normalized_column_name)

            if not isinstance(data_type, str) or not data_type.strip():
                errors.append(
                    f"Column '{column_name}' in '{table_name}' "
                    "must have a data type."
                )

            primary_key = column.get("primary_key", False)

            if not isinstance(primary_key, bool):
                errors.append(
                    f"primary_key for '{column_name}' must be True or False."
                )

    for table in tables:

        if not isinstance(table, dict):
            continue

        columns = table.get("columns", [])

        if not isinstance(columns, list):
            continue

        for column in columns:

            if not isinstance(column, dict):
                continue

            foreign_key = column.get("foreign_key")

            if foreign_key is None:
                continue

            if not isinstance(foreign_key, dict):
                errors.append(
                    f"Invalid foreign key definition in '{table.get('name')}'."
                )
                continue

            referenced_table = foreign_key.get("table")
            referenced_column = foreign_key.get("column")

            if not isinstance(referenced_table, str) or not referenced_table.strip():
                errors.append("Foreign key must specify a referenced table.")
                continue

            if not isinstance(referenced_column, str) or not referenced_column.strip():
                errors.append("Foreign key must specify a referenced column.")
                continue

            target_table = None

            for candidate in tables:
                if (
                    isinstance(candidate, dict)
                    and isinstance(candidate.get("name"), str)
                    and candidate["name"].strip().lower()
                    == referenced_table.strip().lower()
                ):
                    target_table = candidate
                    break

            if target_table is None:
                errors.append(
                    f"Foreign key references unknown table '{referenced_table}'."
                )
                continue

            target_columns = target_table.get("columns", [])

            if not isinstance(target_columns, list):
                continue

            matching_column = None

            for target in target_columns:
                if (
                    isinstance(target, dict)
                    and isinstance(target.get("name"), str)
                    and target["name"].strip().lower()
                    == referenced_column.strip().lower()
                ):
                    matching_column = target
                    break

            if matching_column is None:
                errors.append(
                    f"Foreign key references unknown column "
                    f"'{referenced_column}' in table '{referenced_table}'."
                )
                continue

            if matching_column.get("primary_key") is not True:
                errors.append(
                    f"Referenced column '{referenced_column}' in "
                    f"'{referenced_table}' must be marked as a primary key."
                )

    return errors


def format_schema_for_prompt(schema):
    
    errors = validate_schema(schema)

    if errors:
        raise ValueError(
            "Cannot format an invalid schema: " + "; ".join(errors)
        )

    formatted_schema = []

    for table in schema["tables"]:

        table_name = table["name"]

        formatted_schema.append(f"Table: {table_name}")

        for column in table["columns"]:

            column_name = column["name"]
            data_type = column["type"]

            description = f"  - {column_name}: {data_type}"

            if column.get("primary_key", False):
                description += " (Primary Key)"

            foreign_key = column.get("foreign_key")

            if foreign_key:
                description += (
                    f" (Foreign Key -> "
                    f"{foreign_key['table']}.{foreign_key['column']})"
                )

            formatted_schema.append(description)

        formatted_schema.append("")

    return "\n".join(formatted_schema)
