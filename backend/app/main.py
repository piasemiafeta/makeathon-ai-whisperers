from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import DB_PATH, METRICS_PATH, SCHEMA_PATH, read_text_file, run_sql
from app.models import (
    AskRequest,
    AskResponse,
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


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database_found": DB_PATH.exists(),
        "database_path": str(DB_PATH),
    }


@app.get("/schema")
def get_schema():
    try:
        return {
            "schema": read_text_file(SCHEMA_PATH)
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/metrics")
def get_metrics_dictionary():
    try:
        return {
            "metrics_dictionary": read_text_file(METRICS_PATH)
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/tables")
def get_tables():
    try:
        sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
        LIMIT 100;
        """

        df = run_sql(sql)

        return {
            "tables": df["table_name"].tolist()
        }

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
        df = run_sql(sql)

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