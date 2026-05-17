import argparse
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


# Make backend/app importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


#from backend.app.database import METRICS_PATH, SCHEMA_PATH, read_text_file, run_sql
from backend.app.datasets import DEFAULT_DATASET_ID, get_dataset_paths, list_datasets, read_text_file, run_sql
from backend.app.llm_planner import generate_dashboard_plan
from backend.app.sql_guard import validate_select_sql


mcp = FastMCP(
    "NR2Dashboard MCP Server",
    instructions=(
        "MCP tools for querying the NR2Dashboard banking voicebot dataset. "
        "Use these tools to inspect schema, read metric definitions, generate dashboard plans, "
        "and run validated SELECT SQL against DuckDB."
    ),
)


@mcp.tool()
def get_schema() -> str:
    paths = get_dataset_paths(DEFAULT_DATASET_ID)
    return read_text_file(paths["schema_path"])


@mcp.tool()
def get_metrics_dictionary() -> str:
    paths = get_dataset_paths(DEFAULT_DATASET_ID)
    return read_text_file(paths["metrics_path"])


@mcp.tool()
def list_tables() -> dict[str, Any]:
    """
    List tables and views available in the DuckDB database.
    """
    sql = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'main'
    ORDER BY table_name
    LIMIT 100;
    """

    df = run_sql(sql, DEFAULT_DATASET_ID)

    return {
        "tables": df["table_name"].tolist()
    }


@mcp.tool()
def run_sql_query(sql: str) -> dict[str, Any]:
    """
    Run a validated SELECT SQL query against the DuckDB dataset.
    The query must use allowed views/tables and include LIMIT.
    """
    validate_select_sql(sql)
    df = run_sql(sql, DEFAULT_DATASET_ID)

    return {
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
        "row_count": len(df),
    }

@mcp.tool()
def list_available_datasets() -> dict[str, Any]:
    """
    List datasets registered in NR2Dashboard.
    """
    return {
        "datasets": list_datasets()
    }


@mcp.tool()
def ask(question: str) -> dict[str, Any]:
    """
    Turn a natural-language analytics question into SQL, run it, and return
    chart metadata plus query results.
    """
    plan = generate_dashboard_plan(question)

    sql = plan["sql"]
    chart = plan["chart"]
    explanation = plan.get("explanation", "Generated dashboard result.")

    validate_select_sql(sql)
    df = run_sql(sql, DEFAULT_DATASET_ID)

    return {
        "question": question,
        "sql": sql,
        "chart": chart,
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
        "row_count": len(df),
        "explanation": explanation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NR2Dashboard MCP server.")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run MCP server over HTTP/SSE instead of stdio.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for HTTP/SSE mode.",
    )

    args = parser.parse_args()

    if args.http:
        print(
            "HTTP/SSE mode is not enabled for this MCP SDK version. "
            "Use stdio mode with MCP Inspector instead."
        )
        print("Run: python -m mcp_server.server")
    else:
        mcp.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("MCP server stopped.")