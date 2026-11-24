
import re
from io import BytesIO
from pathlib import Path

import pandas as pd


def normalize_identifier(name):
    """
    Convert a filename or column name into a SQL-friendly identifier.

    Example:
        Customer Details.csv -> customer_details
        Order Amount ($) -> order_amount
    """

    name = str(name).strip().lower()

    # Replace spaces and special characters with underscores.
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

    # Remove consecutive underscores.
    name = re.sub(r"_+", "_", name)

    # Remove underscores at the beginning and end.
    name = name.strip("_")

    if not name:
        name = "unnamed"

    # SQL identifiers should not start with a number.
    if name[0].isdigit():
        name = "column_" + name

    return name


def make_unique_names(names):
    """
    Ensure that normalized column or table names are unique.
    """

    result = []
    used_names = set()

    for name in names:
        base_name = normalize_identifier(name)
        unique_name = base_name
        counter = 2

        while unique_name in used_names:
            unique_name = f"{base_name}_{counter}"
            counter += 1

        used_names.add(unique_name)
        result.append(unique_name)

    return result


def detect_column_type(series):
    """
    Detect a basic SQL-compatible data type from a Pandas column.
    """

    if pd.api.types.is_bool_dtype(series):
        return "INTEGER"

    if pd.api.types.is_integer_dtype(series):
        return "INTEGER"

    if pd.api.types.is_float_dtype(series):
        return "REAL"

    # Dates and other object columns are stored as TEXT in SQLite.
    return "TEXT"


def _read_bytes_as_csv(raw_bytes):
    """Read CSV bytes, trying common encodings (Excel often saves as cp1252)."""
    last_error = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(BytesIO(raw_bytes), encoding=encoding, sep=None, engine="python")
        except UnicodeDecodeError as error:
            last_error = error
    raise last_error


def read_csv_file(uploaded_file):
    """
    Read either a Streamlit uploaded file, a file-like object, or a local CSV path.
    Returns (filename, dataframe).
    """
    try:
        if hasattr(uploaded_file, "getvalue"):
            raw_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name

        elif hasattr(uploaded_file, "read"):
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
            raw_bytes = uploaded_file.read()
            if isinstance(raw_bytes, str):
                raw_bytes = raw_bytes.encode("utf-8")
            filename = getattr(uploaded_file, "name", "dataset.csv")

        else:
            file_path = Path(uploaded_file)
            raw_bytes = file_path.read_bytes()
            filename = file_path.name

        dataframe = _read_bytes_as_csv(raw_bytes)

    except Exception as error:
        raise ValueError(f"Could not read CSV file: {error}") from error

    # Drop columns and rows that are completely empty (common in Excel exports).
    dataframe = dataframe.dropna(axis=1, how="all").dropna(axis=0, how="all")

    if len(dataframe.columns) == 0:
        raise ValueError(f"The file '{filename}' has no columns.")

    if dataframe.empty:
        raise ValueError(f"The file '{filename}' contains no data rows.")

    return filename, dataframe.reset_index(drop=True)


def process_csv_files(uploaded_files):
    """
    Process one or more CSV files.

    Returns:
        {
            "dataframes": {
                "customers": pandas_dataframe
            },
            "schema": {
                "tables": [...]
            },
            "file_mapping": {...}
        }
    """

    if not uploaded_files:
        raise ValueError("Please upload at least one CSV file.")

    dataframes = {}
    tables = []
    file_mapping = {}

    for uploaded_file in uploaded_files:

        filename, dataframe = read_csv_file(uploaded_file)

        # Derive a table name from the filename.
        raw_table_name = Path(filename).stem

        table_name = normalize_identifier(raw_table_name)

        # Prevent duplicate table names.
        base_name = table_name
        counter = 2

        while table_name in dataframes:
            table_name = f"{base_name}_{counter}"
            counter += 1

        # Normalize all column names.
        original_columns = list(dataframe.columns)

        normalized_columns = make_unique_names(
            original_columns
        )

        dataframe.columns = normalized_columns

        # Detect SQL data types.
        columns = []

        for column_name in dataframe.columns:

            column_type = detect_column_type(
                dataframe[column_name]
            )

            columns.append({
                "name": column_name,
                "type": column_type,
                "primary_key": False
            })

        # Store the dataframe using its SQL table name.
        dataframes[table_name] = dataframe

        # Create schema in the existing project format.
        tables.append({
            "name": table_name,
            "columns": columns
        })

        file_mapping[table_name] = {
            "original_filename": filename,
            "original_columns": original_columns,
            "normalized_columns": normalized_columns
        }

    schema = {
        "tables": tables
    }

    return {
        "dataframes": dataframes,
        "schema": schema,
        "file_mapping": file_mapping
    }
