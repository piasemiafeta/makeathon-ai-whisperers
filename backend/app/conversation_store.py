from collections import defaultdict
from typing import Any
from uuid import uuid4


MAX_TURNS_PER_SESSION = 8

_sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)


def create_session_id() -> str:
    return str(uuid4())


def get_history(session_id: str | None) -> list[dict[str, Any]]:
    if not session_id:
        return []

    return _sessions.get(session_id, [])[-MAX_TURNS_PER_SESSION:]


def add_turn(
    session_id: str,
    question: str,
    sql: str,
    chart: dict[str, Any],
    explanation: str,
) -> None:
    _sessions[session_id].append(
        {
            "question": question,
            "sql": sql,
            "chart": chart,
            "explanation": explanation,
        }
    )

    _sessions[session_id] = _sessions[session_id][-MAX_TURNS_PER_SESSION:]


def reset_session(session_id: str) -> bool:
    if session_id in _sessions:
        del _sessions[session_id]
        return True

    return False


def format_history_for_prompt(history: list[dict[str, Any]]) -> str:
    if not history:
        return "No previous conversation context."

    lines = []

    for index, turn in enumerate(history, start=1):
        chart = turn.get("chart", {})

        lines.append(
            f"""
Turn {index}
User question: {turn.get("question")}
SQL used: {turn.get("sql")}
Chart type: {chart.get("chart_type")}
Chart title: {chart.get("title")}
Explanation: {turn.get("explanation")}
""".strip()
        )

    return "\n\n".join(lines)