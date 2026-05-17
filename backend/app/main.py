from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

#from app.database import DB_PATH, METRICS_PATH, SCHEMA_PATH, read_text_file, run_sql
from app.datasets import (
    DEFAULT_DATASET_ID,
    get_dataset_paths,
    list_datasets,
    read_text_file,
    run_sql,
)
from app.models import (
    AskRequest,
    AskResponse,
    DatasetsResponse,
    QueryRequest,
    QueryResponse,
    ResetSessionRequest,
    ResetSessionResponse,
)

from app.sql_guard import ALLOWED_TABLES, validate_select_sql
from app.llm_planner import generate_dashboard_plan
import os
from app.conversation_store import (
    add_turn,
    create_session_id,
    format_history_for_prompt,
    get_history,
    reset_session,
)

app = FastAPI(
    title="NR2Dashboard API",
    description="Backend API for natural-language dashboard generation over the banking voicebot dataset.",
    version="0.2.0",
)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "NR2Dashboard API is running.",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/datasets", response_model=DatasetsResponse)
def get_datasets():
    return {
        "datasets": list_datasets()
    }

@app.get("/health")
def health():
    paths = get_dataset_paths(DEFAULT_DATASET_ID)

    return {
        "status": "ok",
        "default_dataset_id": DEFAULT_DATASET_ID,
        "database_found": paths["database_path"].exists(),
        "database_path": str(paths["database_path"]),
    }


@app.get("/schema")
def get_schema(dataset_id: str | None = None):
    try:
        paths = get_dataset_paths(dataset_id)

        return {
            "dataset_id": dataset_id or DEFAULT_DATASET_ID,
            "schema": read_text_file(paths["schema_path"]),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/metrics")
def get_metrics_dictionary(dataset_id: str | None = None):
    try:
        paths = get_dataset_paths(dataset_id)

        return {
            "dataset_id": dataset_id or DEFAULT_DATASET_ID,
            "metrics_dictionary": read_text_file(paths["metrics_path"]),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/tables")
def get_tables(dataset_id: str | None = None):
    try:
        sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
        LIMIT 100;
        """

        df = run_sql(sql, dataset_id)

        return {
            "dataset_id": dataset_id or DEFAULT_DATASET_ID,
            "tables": df["table_name"].tolist()
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/columns/{table_name}")
def get_columns(table_name: str):
    if table_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail="Table/view is not allowed.")

    try:
        sql = f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        LIMIT 200;
        """

        df = run_sql(sql)

        return {
            "table": table_name,
            "columns": df.to_dict(orient="records"),
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/query", response_model=QueryResponse)
def query_database(payload: QueryRequest):
    try:
        validate_select_sql(payload.sql)
        df = run_sql(payload.sql)

        return {
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "row_count": len(df),
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest):
    try:
        session_id = payload.session_id or create_session_id()

        history = get_history(session_id)
        history_context = format_history_for_prompt(history)

        plan = generate_dashboard_plan(
            question=payload.question,
            history_context=history_context,
        )

        sql = plan["sql"]
        chart = plan["chart"]
        explanation = plan.get("explanation", "Generated dashboard result.")

        validate_select_sql(sql)
        df = run_sql(sql, payload.dataset_id)

        add_turn(
            session_id=session_id,
            question=payload.question,
            sql=sql,
            chart=chart,
            explanation=explanation,
        )

        return {
            "question": payload.question,
            "session_id": session_id,
            "dataset_id": payload.dataset_id or DEFAULT_DATASET_ID,
            "sql": sql,
            "chart": chart,
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "row_count": len(df),
            "explanation": explanation,
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except KeyError as exc:
        raise HTTPException(status_code=500, detail=f"Planner response missing key: {exc}")

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    
@app.post("/session/reset", response_model=ResetSessionResponse)
def reset_conversation_session(payload: ResetSessionRequest):
    was_reset = reset_session(payload.session_id)

    return {
        "session_id": payload.session_id,
        "reset": was_reset,
    }