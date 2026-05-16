from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    sql: str = Field(..., description="A safe SELECT SQL query.")


class QueryResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int


class AskRequest(BaseModel):
    question: str = Field(..., description="Natural-language user question.")


class ChartSpec(BaseModel):
    chart_type: str
    title: str
    x: str | None = None
    y: str | None = None
    category: str | None = None
    value: str | None = None


class AskResponse(BaseModel):
    question: str
    sql: str
    chart: ChartSpec
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    explanation: str