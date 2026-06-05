import pandas as pd
import numpy as np


def detect_outliers(column):
    q1 = column.quantile(0.25)
    q3 = column.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return column[(column < lower) | (column > upper)]


def validate_dataframe(df):
    """Return validation reports for a cleaned DataFrame."""
    report = {
        "invalid_cells": [],
        "anomalies": [],
        "range_warnings": [],
    }

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            invalid_mask = ~df[col].between(-1e6, 1e6)
            if invalid_mask.any():
                report["invalid_cells"].append(
                    {
                        "column": col,
                        "invalid_values": df.loc[invalid_mask, col].dropna().unique().tolist(),
                    }
                )

            outliers = detect_outliers(df[col].dropna())
            if not outliers.empty:
                report["anomalies"].append(
                    {
                        "column": col,
                        "count": int(outliers.count()),
                        "sample_values": outliers.head(5).tolist(),
                    }
                )

            if df[col].min() < 0 and df[col].max() > 10000:
                report["range_warnings"].append(
                    {
                        "column": col,
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "message": "Large numeric range detected that may indicate inconsistent units.",
                    }
                )

    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if missing_count > 0:
            report["range_warnings"].append(
                {
                    "column": col,
                    "message": f"{missing_count} missing values were detected after cleaning.",
                }
            )

    return report
