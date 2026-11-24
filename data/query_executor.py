import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import sqlite3
import time

import pandas as pd

from validation.sql_validator import validate_sql


def _read_only_authorizer(action, arg1, arg2, database_name, source):
    """
    Allow only operations needed for read-only queries.

    All database modifications and schema changes are denied.
    """

    allowed_actions = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
    }

    # Some Python/SQLite versions expose this action.
    if hasattr(sqlite3, "SQLITE_RECURSIVE"):
        allowed_actions.add(sqlite3.SQLITE_RECURSIVE)

    if action in allowed_actions:
        return sqlite3.SQLITE_OK

    return sqlite3.SQLITE_DENY


def execute_query(
    sql,
    dataframes,
    schema,
    max_rows=1000,
    timeout_seconds=10
):
    """
    Validate and execute a read-only SQL query against
    CSV data loaded into an in-memory SQLite database.

    Returns a dictionary containing:
        success
        dataframe
        row_count
        truncated
        execution_time
        validation
        error
    """

    start_time = time.monotonic()

    # Check execution settings.
    if not isinstance(max_rows, int) or max_rows < 1:
        return {
            "success": False,
            "error": "max_rows must be a positive integer.",
            "dataframe": None
        }

    if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        return {
            "success": False,
            "error": "timeout_seconds must be positive.",
            "dataframe": None
        }

    if not isinstance(dataframes, dict) or not dataframes:
        return {
            "success": False,
            "error": "No CSV datasets are available for execution.",
            "dataframe": None
        }

    # Validate the SQL using the existing SQL validator.
    validation = validate_sql(
        sql,
        schema,
        dialect="sqlite"
    )

    if not validation["valid"]:
        return {
            "success": False,
            "error": "SQL validation failed.",
            "validation": validation,
            "dataframe": None
        }

    # Make sure every schema table has corresponding data.
    schema_table_names = {
        table["name"].lower()
        for table in schema["tables"]
    }

    dataframe_table_names = {
        name.lower()
        for name in dataframes
    }

    if schema_table_names != dataframe_table_names:
        return {
            "success": False,
            "error": (
                "The uploaded DataFrames do not match "
                "the supplied database schema."
            ),
            "dataframe": None
        }

    connection = None

    try:
        # Create a temporary in-memory database.
        connection = sqlite3.connect(":memory:")

        # Load each CSV DataFrame as a SQLite table.
        for table_name, dataframe in dataframes.items():

            if not isinstance(dataframe, pd.DataFrame):
                raise ValueError(
                    f"Table '{table_name}' is not a Pandas DataFrame."
                )

            dataframe.to_sql(
                name=table_name,
                con=connection,
                index=False,
                if_exists="fail"
            )

        # Prevent modification of the database.
        connection.set_authorizer(
            _read_only_authorizer
        )

        # Add a time limit to SQL execution.
        deadline = time.monotonic() + timeout_seconds

        def stop_if_too_slow():
            return int(time.monotonic() > deadline)

        connection.set_progress_handler(
            stop_if_too_slow,
            1000
        )

        cursor = connection.cursor()

        # Execute the validated query.
        cursor.execute(sql)

        if cursor.description is None:
            raise ValueError(
                "The query did not return a result table."
            )

        column_names = [
            description[0]
            for description in cursor.description
        ]

        # Fetch one extra row to detect result truncation.
        rows = cursor.fetchmany(max_rows + 1)

        truncated = len(rows) > max_rows

        # Display only the permitted number of rows.
        rows = rows[:max_rows]

        result_dataframe = pd.DataFrame(
            rows,
            columns=column_names
        )

        execution_time = time.monotonic() - start_time

        return {
            "success": True,
            "dataframe": result_dataframe,
            "row_count": len(result_dataframe),
            "truncated": truncated,
            "execution_time": round(execution_time, 4),
            "validation": validation,
            "error": None
        }

    except sqlite3.OperationalError as error:

        error_message = str(error)

        if "interrupted" in error_message.lower():
            error_message = (
                "Query execution exceeded the time limit."
            )

        return {
            "success": False,
            "error": error_message,
            "dataframe": None,
            "validation": validation
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error),
            "dataframe": None,
            "validation": validation
        }

    finally:
        if connection is not None:
            connection.close()
