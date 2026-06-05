"""Data analysis utilities for statistical summaries and trend discovery."""

import pandas as pd


def summary_statistics(df):
    stats = df.select_dtypes(include=["number"]).describe().transpose()
    return stats.round(3).to_dict(orient="index")


def correlation_summary(df):
    numeric = df.select_dtypes(include=["number"])
    if numeric.shape[1] < 2:
        return {}
    correlation = numeric.corr()
    return correlation.round(3).to_dict()


def trend_analysis(df):
    results = []
    numeric = df.select_dtypes(include=["number"])
    if numeric.empty:
        return results

    for column in numeric.columns:
        values = numeric[column].dropna()
        if len(values) < 4:
            continue
        slope = pd.Series(values).pct_change().mean()
        results.append(
            {
                "column": column,
                "average_change": float(slope),
                "direction": "increasing" if slope >= 0 else "decreasing",
            }
        )
    return results


def analyze_dataframe(df):
    summary = summary_statistics(df)
    trends = trend_analysis(df)
    categories = df.select_dtypes(include=["object"]).nunique().to_dict()
    return {
        "summary_statistics": summary,
        "trend_analysis": trends,
        "category_counts": categories,
    }
