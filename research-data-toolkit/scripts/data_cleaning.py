"""Data cleaning utilities for research dataset processing."""

import pandas as pd
import numpy as np


def _standardize_column_names(columns):
    return [str(col).strip().lower().replace(" ", "_") for col in columns]


def _guess_date_columns(df):
    date_columns = []
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            date_columns.append(col)
    return date_columns


def clean_dataframe(df, sample_rows=5):
    """Clean a raw DataFrame and return summary metadata."""
    output = df.copy()
    output.columns = _standardize_column_names(output.columns)
    output = output.drop_duplicates(ignore_index=True)

    for col in output.columns:
        if output[col].dtype == object:
            output[col] = output[col].astype(str).str.strip()
            output[col] = output[col].replace({"nan": np.nan, "none": np.nan, "na": np.nan})

    for col in output.select_dtypes(include=["number"]).columns:
        median_value = output[col].median()
        output[col] = output[col].fillna(median_value)

    for col in _guess_date_columns(output):
        try:
            output[col] = pd.to_datetime(output[col], errors="coerce")
        except Exception:
            pass

    if output.isna().sum().sum() > 0:
        output = output.fillna(method="ffill").fillna(method="bfill")

    summary = {
        "rows": int(output.shape[0]),
        "columns": int(output.shape[1]),
        "duplicate_rows_removed": int(df.shape[0] - output.shape[0]),
        "missing_values_after_cleaning": int(output.isna().sum().sum()),
        "preview": output.head(sample_rows).fillna("N/A").to_dict(orient="records"),
    }
    return output, summary
