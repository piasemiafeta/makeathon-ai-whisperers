from typing import Any

import pandas as pd


def infer_chart_spec(question: str, df: pd.DataFrame) -> dict[str, Any]:
    q = question.lower()
    columns = list(df.columns)

    if df.empty:
        return {
            "chart_type": "table",
            "title": "No results",
        }

    if len(columns) == 1 and len(df) == 1:
        return {
            "chart_type": "metric",
            "title": "Metric result",
            "value": columns[0],
        }

    if "pie" in q or "donut" in q or "πίτα" in q:
        return {
            "chart_type": "pie",
            "title": "Distribution",
            "category": columns[0],
            "value": columns[1] if len(columns) > 1 else None,
        }

    if (
        "trend" in q
        or "daily" in q
        or "over time" in q
        or "ημερήσια" in q
        or "τάση" in q
        or "ανά ημέρα" in q
    ):
        return {
            "chart_type": "line",
            "title": "Trend over time",
            "x": columns[0],
            "y": columns[1] if len(columns) > 1 else None,
        }

    if len(columns) >= 2:
        return {
            "chart_type": "bar",
            "title": "Breakdown",
            "x": columns[0],
            "y": columns[1],
        }

    return {
        "chart_type": "table",
        "title": "Results table",
    }