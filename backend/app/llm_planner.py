import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

#from app.database import METRICS_PATH, SCHEMA_PATH, read_text_file
from app.datasets import DEFAULT_DATASET_ID, get_dataset_paths, read_text_file


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("The LLM did not return valid JSON.")

    return json.loads(text[start:end + 1])


def generate_dashboard_plan(question: str, history_context: str | None = None) -> dict[str, Any]:
    paths = get_dataset_paths(DEFAULT_DATASET_ID)
    schema = read_text_file(paths["schema_path"])
    metrics = read_text_file(paths["metrics_path"])

    system_prompt = f"""
You are an analytics planner for a banking voicebot dashboard.

You receive a natural-language question in English or Greek.
Your job is to produce a safe dashboard plan as JSON.

Use only the provided DuckDB schema and metric definitions.

DATABASE SCHEMA:
{schema}

METRIC DEFINITIONS:
{metrics}

Rules:
- Return JSON only. No markdown.
- Use only SELECT SQL.
- Use only these views unless truly necessary: v_conversations, v_turns, v_evaluations, v_data_collection, v_tool_calls.
- Always include LIMIT.
- Do not modify data.
- Do not invent columns.
- Prefer flat views over conversations_raw.
- If the user asks in Greek, you may still output English SQL aliases.
- Choose chart_type from: bar, line, pie, donut, table, metric.
- For line charts, x should be the date/time column and y should be the numeric metric column.
- For trends over time, use line.
- For distributions, use bar or pie/donut.
- For rankings, use bar.
- For single KPI values, use metric.
- For daily trends, always use start_date from v_conversations, not EXTRACT(DAY FROM start_time).
- For weekly/monthly trends, use DATE_TRUNC('week', start_time) or DATE_TRUNC('month', start_time).
- Never group by only day-of-month unless the user explicitly asks for day of month.
- Use descriptive aliases like conversations, avg_csat, containment_rate, escalation_rate.
- Avoid aliases named count.
- If the user asks for "last 7 days", filter with start_date >= CURRENT_DATE - INTERVAL 7 DAY.
- If the user asks for "last 30 days", filter with start_date >= CURRENT_DATE - INTERVAL 30 DAY.
- If no time range is specified for a trend, show the full available period ordered by date.
- Do not describe LIMIT as a time filter. LIMIT only caps the number of returned rows.
- If no date filter is present in the SQL, say "available dataset period", not "last N days".
- Since v_conversations already has start_date, use start_date directly for daily trends.
- For daily trends, prefer: SELECT start_date, COUNT(*) AS conversations FROM v_conversations GROUP BY start_date ORDER BY start_date LIMIT 100;
- Never use dynamic_variables.segment, dynamic_variables.region, or nested metadata paths when the same fields exist in flat views.
- In v_conversations, use segment, region, csat_score, outcome, bot_version, main_language, start_date directly.
- For CSAT by segment, prefer:
  SELECT segment, ROUND(AVG(csat_score), 2) AS avg_csat
  FROM v_conversations
  WHERE csat_score IS NOT NULL
  GROUP BY segment
  ORDER BY avg_csat DESC
  LIMIT 100;

- Do not use CURRENT_DATE for relative time ranges because the dataset is synthetic and may not match today's real date.
- For "this week", "last 7 days", or Greek equivalents, use the latest available date in the dataset:
  WHERE start_date >= (SELECT MAX(start_date) FROM v_conversations) - INTERVAL 6 DAY
- For "last 30 days", use:
  WHERE start_date >= (SELECT MAX(start_date) FROM v_conversations) - INTERVAL 30 DAY

- Avoid aliases named count. Use descriptive aliases such as conversations, escalated_calls, avg_latency_ms, failure_rate.
- Round averages and percentages to 2 decimal places.

- Important semantic note: evaluation criterion escalation_triggered measures whether escalation happened; it is a state, not automatically a quality failure.
- When asked for general failure rate by evaluation criterion, either include all criteria but mention this caveat in the explanation, or exclude escalation_triggered if the user asks for quality failures.

- When calculating rates, return percentages by multiplying by 100.0 and use aliases ending in _pct, e.g. escalation_rate_pct, containment_rate_pct, failure_rate_pct.
- Do not call a decimal value like 0.11 a percentage. If the explanation says percentage, the SQL must multiply by 100.0.

- You may receive previous conversation context. Use it only when the current question is a follow-up.
- Follow-up examples include: "make it a bar chart", "show it by region", "κάν' το line chart", "δείξε το ανά περιοχή".
- If the user asks to change only the chart type, keep the previous SQL logic when appropriate and only change the chart spec.
- If the user asks to change the grouping/dimension, generate a new SQL query using the same metric or topic from the previous turn.

Examples:

User: Which customer segments have the highest average CSAT?
JSON:
{{
  "sql": "SELECT segment, ROUND(AVG(csat_score), 2) AS avg_csat FROM v_conversations WHERE csat_score IS NOT NULL GROUP BY segment ORDER BY avg_csat DESC LIMIT 100;",
  "chart": {{
    "chart_type": "bar",
    "title": "Average CSAT by Customer Segment",
    "x": "segment",
    "y": "avg_csat",
    "category": "segment",
    "value": "avg_csat"
  }},
  "explanation": "Average CSAT by customer segment, excluding conversations without a survey score."
}}

User: How is the bot doing this week?
JSON:
{{
  "sql": "SELECT start_date, COUNT(*) AS conversations FROM v_conversations WHERE start_date >= (SELECT MAX(start_date) FROM v_conversations) - INTERVAL 6 DAY GROUP BY start_date ORDER BY start_date LIMIT 100;",
  "chart": {{
    "chart_type": "line",
    "title": "Conversation Volume in the Latest 7 Days",
    "x": "start_date",
    "y": "conversations",
    "category": null,
    "value": null
  }},
  "explanation": "Daily conversation volume for the latest 7 days available in the dataset."
}}

User: Show failure rate by evaluation criterion
JSON:
{{
  "sql": "SELECT criterion_id, ROUND(100.0 * AVG(CASE WHEN result = 'failure' THEN 1.0 WHEN result = 'success' THEN 0.0 ELSE NULL END), 2) AS failure_rate_pct FROM v_evaluations WHERE result IN ('success', 'failure') GROUP BY criterion_id ORDER BY failure_rate_pct DESC LIMIT 100;",
  "chart": {{
    "chart_type": "bar",
    "title": "Failure Rate by Evaluation Criterion",
    "x": "criterion_id",
    "y": "failure_rate_pct",
    "category": "criterion_id",
    "value": "failure_rate_pct"
  }},
  "explanation": "Failure rate percentage by evaluation criterion, excluding unknown results. Note: escalation_triggered indicates whether escalation happened and is not automatically a quality failure."
}}

User: Which customer segments have the highest escalation rate?
JSON:
{{
  "sql": "SELECT segment, ROUND(100.0 * AVG(CASE WHEN outcome = 'escalated' THEN 1.0 ELSE 0.0 END), 2) AS escalation_rate_pct FROM v_conversations GROUP BY segment ORDER BY escalation_rate_pct DESC LIMIT 100;",
  "chart": {{
    "chart_type": "bar",
    "title": "Escalation Rate by Customer Segment",
    "x": "segment",
    "y": "escalation_rate_pct",
    "category": "segment",
    "value": "escalation_rate_pct"
  }},
  "explanation": "Escalation rate percentage by customer segment."
}}

Required JSON shape:
{{
  "sql": "SELECT ... LIMIT 100;",
  "chart": {{
    "chart_type": "bar",
    "title": "Clear chart title",
    "x": "column_name_or_null",
    "y": "column_name_or_null",
    "category": "column_name_or_null",
    "value": "column_name_or_null"
  }},
  "explanation": "One short sentence explaining what the result shows."
}}
"""

    user_prompt = f"""
    Previous conversation context:
    {history_context or "No previous conversation context."}

    Current user question:
    {question}

    Return only valid JSON.
    """

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""
    return _extract_json(content)