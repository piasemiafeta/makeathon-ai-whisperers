from pathlib import Path

import duckdb
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "conversations.duckdb"
SCHEMA_PATH = DATA_DIR / "schema.md"
METRICS_PATH = DATA_DIR / "metrics_dictionary.md"


def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB database not found at: {DB_PATH}")

    return duckdb.connect(str(DB_PATH), read_only=True)


def run_sql(sql: str) -> pd.DataFrame:
    with get_connection() as con:
        return con.execute(sql).fetchdf()


def read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found at: {path}")

    return path.read_text(encoding="utf-8")