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
    session_id: str | None = Field(
        default=None,
        description="Optional conversation session id for follow-up questions.",
    )
    dataset_id: str | None = Field(
        default=None,
        description="Optional dataset id. Defaults to the banking voicebot dataset.",
    )

class ChartSpec(BaseModel):
    chart_type: str
    title: str
    x: str | None = None
    y: str | None = None
    category: str | None = None
    value: str | None = None


class AskResponse(BaseModel):
    question: str
    session_id: str
    dataset_id: str
    sql: str
    chart: ChartSpec
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    explanation: str

class ResetSessionRequest(BaseModel):
    session_id: str


class ResetSessionResponse(BaseModel):
    session_id: str
    reset: bool

class DatasetInfo(BaseModel):
    id: str
    name: str
    description: str
    default: bool = False
    database_found: bool = False


class DatasetsResponse(BaseModel):
    datasets: list[DatasetInfo]