import sqlparse


FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
    "attach",
    "detach",
    "copy",
    "pragma",
}

ALLOWED_TABLES = {
    "v_conversations",
    "v_turns",
    "v_evaluations",
    "v_data_collection",
    "v_tool_calls",
    "conversations_raw",
}


def validate_select_sql(sql: str) -> None:
    cleaned = sql.strip()

    if not cleaned:
        raise ValueError("SQL query is empty.")

    parsed = sqlparse.parse(cleaned)

    if len(parsed) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    first_token = parsed[0].token_first(skip_cm=True)

    if not first_token or first_token.value.lower() != "select":
        raise ValueError("Only SELECT queries are allowed.")

    lowered = cleaned.lower()

    for keyword in FORBIDDEN_KEYWORDS:
        if f" {keyword} " in f" {lowered} ":
            raise ValueError(f"Forbidden SQL keyword used: {keyword}")

    uses_allowed_table = any(table in lowered for table in ALLOWED_TABLES)

    if not uses_allowed_table:
        raise ValueError("Query must use one of the allowed dataset tables/views.")

    if "limit" not in lowered:
        raise ValueError("Query must include a LIMIT clause.")