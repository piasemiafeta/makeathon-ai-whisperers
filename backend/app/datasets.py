import os
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
REPO_DIR = BACKEND_DIR.parent

DUCKDB_PATH_ENV = os.getenv("DUCKDB_PATH")

DATA_DIR_CANDIDATES = [
    BACKEND_DIR / "data",       # Railway, because Root Directory = backend
    REPO_DIR / "data",          # Local repo root
    Path.cwd() / "data",        # Current working directory fallback
    Path("/app/data"),          # Railway-like fallback
    Path("/app/backend/data"),  # Alternative Railway-like fallback
]

DATA_DIR = next(
    (
        path
        for path in DATA_DIR_CANDIDATES
        if (path / "conversations.duckdb").exists()
    ),
    BACKEND_DIR / "data",
)

DATABASE_PATH = (
    Path(DUCKDB_PATH_ENV)
    if DUCKDB_PATH_ENV
    else DATA_DIR / "conversations.duckdb"
)

DEFAULT_DATASET_ID = "banking_voicebot"

DATASETS: dict[str, dict[str, Any]] = {
    DEFAULT_DATASET_ID: {
        "id": DEFAULT_DATASET_ID,
        "name": "Banking Voicebot Conversations",
        "description": "90-day synthetic dataset with approximately 10,000 banking voicebot conversations.",
        "database_path": DATABASE_PATH,
        "schema_path": DATA_DIR / "schema.md",
        "metrics_path": DATA_DIR / "metrics_dictionary.md",
        "default": True,
    }
}


def list_datasets() -> list[dict[str, Any]]:
    datasets = []

    for dataset in DATASETS.values():
        datasets.append(
            {
                "id": dataset["id"],
                "name": dataset["name"],
                "description": dataset["description"],
                "default": dataset.get("default", False),
                "database_found": Path(dataset["database_path"]).exists(),
            }
        )

    return datasets


def get_dataset(dataset_id: str | None = None) -> dict[str, Any]:
    selected_id = dataset_id or DEFAULT_DATASET_ID

    if selected_id not in DATASETS:
        raise ValueError(f"Unknown dataset_id: {selected_id}")

    return DATASETS[selected_id]


def get_dataset_paths(dataset_id: str | None = None) -> dict[str, Path]:
    dataset = get_dataset(dataset_id)

    return {
        "database_path": Path(dataset["database_path"]),
        "schema_path": Path(dataset["schema_path"]),
        "metrics_path": Path(dataset["metrics_path"]),
    }


def read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found at: {path}")

    return path.read_text(encoding="utf-8")


def get_connection(dataset_id: str | None = None):
    paths = get_dataset_paths(dataset_id)
    db_path = paths["database_path"]

    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB database not found at: {db_path}")

    return duckdb.connect(str(db_path), read_only=True)


def run_sql(sql: str, dataset_id: str | None = None) -> pd.DataFrame:
    with get_connection(dataset_id) as con:
        return con.execute(sql).fetchdf()