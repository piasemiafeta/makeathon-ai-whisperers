import { useState } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Send,
  Database,
  Sparkles,
  Table2,
  Code2,
  Copy,
  Check,
  BarChart3,
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const EXAMPLE_PROMPTS = [
  "Show Greek vs English conversations as a pie chart",
  "Δείξε μου την ημερήσια τάση συνομιλιών",
  "Which customer segments have the highest average CSAT?",
  "Show failure rate by evaluation criterion",
  "Which regions have the most escalated calls?",
  "How is the bot doing this week?",
];
const CHART_COLORS = [
  "#4f46e5",
  "#06b6d4",
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
];

function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copiedSql, setCopiedSql] = useState(false);

  async function askQuestion(customQuestion) {
    const finalQuestion = customQuestion || question;

    if (!finalQuestion.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);
    setCopiedSql(false);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: finalQuestion }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong.");
      }

      setResult(data);
      setQuestion(finalQuestion);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    askQuestion();
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="badge">
          <Sparkles size={16} />
          Natural Language to Dashboard
        </div>

        <h1>NR2Dashboard</h1>
        <p>
          Ask questions in English or Greek and generate live dashboard
          components over the banking voicebot dataset.
        </p>
      </header>

      <main className="layout">
        <section className="panel question-panel">
          <div className="panel-title">
            <Database size={18} />
            Ask your data
          </div>

          <form onSubmit={handleSubmit} className="ask-form">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Show Greek vs English conversations as a pie chart"
              rows={4}
            />

            <button type="submit" disabled={loading}>
              <Send size={16} />
              {loading ? "Thinking..." : "Generate dashboard"}
            </button>
          </form>

          <div className="examples">
            <p>Try one:</p>
            {EXAMPLE_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => askQuestion(prompt)}
                disabled={loading}
              >
                {prompt}
              </button>
            ))}
          </div>
        </section>

        <section className="panel result-panel">
          {loading && (
            <div className="empty-state">
              <div className="loader" />
              <h2>Building your dashboard</h2>
              <p>Generating SQL, querying DuckDB, and preparing the chart.</p>
            </div>
          )}

          {!loading && !result && !error && (
            <div className="empty-state">
              <Sparkles size={34} />
              <h2>Your dashboard will appear here</h2>
              <p>Start with one of the examples or ask your own question.</p>
            </div>
          )}

          {error && (
            <div className="error-box">
              <strong>Error</strong>
              <p>{error}</p>
            </div>
          )}

          {result && (
            <>
              <div className="result-header">
                <div>
                  <p className="eyebrow">Question</p>
                  <h2>{result.question}</h2>
                </div>
              </div>

              <div className="insight-box">
                <strong>Insight</strong>
                <p>{result.explanation}</p>
              </div>

              <ResultStats result={result} />
              <ChartRenderer result={result} />

              <div className="details-grid">
                <SqlPreview sql={result.sql} />
                <DataTable result={result} />
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}

function ChartRenderer({ result }) {
  const { chart, rows } = result;

  if (!rows || rows.length === 0) {
    return (
      <div className="chart-card">
        <h3>{chart.title}</h3>
        <p>No rows returned for this question.</p>
      </div>
    );
  }

  const chartType = chart.chart_type;
  const xKey = chart.x || chart.category;
  const yKey = chart.y || chart.value;

  const formattedRows = rows.map((row) => ({
    ...row,
    [xKey]: formatLabel(row[xKey]),
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>{chart.title}</h3>
        <span>{chartType}</span>
      </div>

      <div className="chart-container">
        {chartType === "bar" && (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={formattedRows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis tickFormatter={(value) => formatAxisTick(value, yKey)} />
              <Tooltip formatter={(value) => formatTooltipValue(value, yKey)} />
              <Bar dataKey={yKey} radius={[8, 8, 0, 0]}>
                {rows.map((_, index) => (
                  <Cell
                    key={`bar-cell-${index}`}
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}

        {chartType === "line" && (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={formattedRows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis tickFormatter={(value) => formatAxisTick(value, yKey)} />
              <Tooltip formatter={(value) => formatTooltipValue(value, yKey)} />
              <Line
                type="monotone"
                dataKey={yKey}
                stroke={CHART_COLORS[0]}
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}

        {(chartType === "pie" || chartType === "donut") && (
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={formattedRows}
                dataKey={yKey}
                nameKey={xKey}
                innerRadius={chartType === "donut" ? 70 : 0}
                outerRadius={110}
                label
              >
                {rows.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}

        {chartType === "metric" && (
          <div className="metric-card">
            <span>{yKey || result.columns?.[0]}</span>
            <strong>{rows[0]?.[yKey] || Object.values(rows[0] || {})[0]}</strong>
          </div>
        )}

        {chartType === "table" && <DataTable result={result} compact />}
      </div>
    </div>
  );
}

function ResultStats({ result }) {
  const chartType = result.chart?.chart_type?.toUpperCase() || "CHART";
  const rowCount = result.row_count ?? result.rows?.length ?? 0;
  const columnCount = result.columns?.length ?? 0;

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <span>Rows</span>
        <strong>{rowCount}</strong>
      </div>

      <div className="stat-card">
        <span>Columns</span>
        <strong>{columnCount}</strong>
      </div>

      <div className="stat-card">
        <span>Visualization</span>
        <strong>{chartType}</strong>
      </div>
    </div>
  );
}

function SqlPreview({ sql }) {
  const [copied, setCopied] = useState(false);

  async function copySql() {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="detail-card">
      <div className="detail-title split">
        <span>
          <Code2 size={16} />
          SQL generated
        </span>

        <button className="copy-button" onClick={copySql} type="button">
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      <pre>{sql}</pre>
    </div>
  );
}

function DataTable({ result, compact = false }) {
  const rows = result.rows || [];
  const columns = result.columns || [];

  return (
    <div className={compact ? "table-wrapper compact" : "detail-card"}>
      {!compact && (
        <div className="detail-title">
          <Table2 size={16} />
          Results preview
        </div>
      )}

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.slice(0, 12).map((row, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column}>{formatCell(row[column])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!compact && rows.length > 12 && (
        <p className="table-note">Showing 12 of {rows.length} rows.</p>
      )}
    </div>
  );
}

function formatCell(value) {
  if (value === null || value === undefined) return "—";

  if (value === "el") return "Greek";
  if (value === "en") return "English";

  if (typeof value === "number") {
    return Number.isInteger(value) ? value : value.toFixed(2);
  }

  if (typeof value === "string" && value.includes("T00:00:00")) {
    return value.split("T")[0];
  }

  return String(value);
}

function formatLabel(value) {
  if (value === "el") return "Greek";
  if (value === "en") return "English";

  if (typeof value === "string" && value.includes("T00:00:00")) {
    return value.split("T")[0];
  }

  return value;
}

function isPercentKey(key) {
  return key && (key.includes("_pct") || key.includes("rate"));
}

function formatAxisTick(value, key) {
  if (typeof value === "number" && isPercentKey(key)) {
    return `${value}%`;
  }

  return value;
}

function formatTooltipValue(value, key) {
  if (typeof value === "number" && isPercentKey(key)) {
    return [`${value.toFixed(2)}%`, key];
  }

  if (typeof value === "number") {
    return [Number.isInteger(value) ? value : value.toFixed(2), key];
  }

  return [value, key];
}

export default App;