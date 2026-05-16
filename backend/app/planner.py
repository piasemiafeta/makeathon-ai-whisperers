def temporary_question_to_sql(question: str) -> tuple[str, str]:
    q = question.lower()

    if "daily" in q or "trend" in q or "ημερήσια" in q or "τάση" in q or "ανά ημέρα" in q:
        sql = """
        SELECT
            start_date,
            COUNT(*) AS conversations
        FROM v_conversations
        GROUP BY start_date
        ORDER BY start_date
        LIMIT 100;
        """
        explanation = "Showing daily conversation volume."

    elif "language" in q or "γλώσσα" in q or "greek" in q or "english" in q or "ελληνικά" in q or "αγγλικά" in q:
        sql = """
        SELECT
            main_language,
            COUNT(*) AS conversations
        FROM v_conversations
        GROUP BY main_language
        ORDER BY conversations DESC
        LIMIT 100;
        """
        explanation = "Showing conversation volume by detected main language."

    elif "bot version" in q or "version" in q or "έκδοση" in q:
        sql = """
        SELECT
            bot_version,
            COUNT(*) AS conversations
        FROM v_conversations
        GROUP BY bot_version
        ORDER BY conversations DESC
        LIMIT 100;
        """
        explanation = "Showing conversation volume by bot version."

    elif "region" in q or "περιοχή" in q:
        sql = """
        SELECT
            region,
            COUNT(*) AS conversations
        FROM v_conversations
        GROUP BY region
        ORDER BY conversations DESC
        LIMIT 100;
        """
        explanation = "Showing conversation volume by region."

    elif "segment" in q or "customer segment" in q or "κατηγορία πελάτη" in q:
        sql = """
        SELECT
            segment,
            COUNT(*) AS conversations
        FROM v_conversations
        GROUP BY segment
        ORDER BY conversations DESC
        LIMIT 100;
        """
        explanation = "Showing conversation volume by customer segment."

    elif "csat" in q or "satisfaction" in q or "ικανοποίηση" in q:
        sql = """
        SELECT
            segment,
            ROUND(AVG(csat_score), 2) AS avg_csat
        FROM v_conversations
        WHERE csat_score IS NOT NULL
        GROUP BY segment
        ORDER BY avg_csat DESC
        LIMIT 100;
        """
        explanation = "Showing average CSAT by customer segment, excluding missing survey scores."

    elif "outcome" in q or "resolved" in q or "escalated" in q or "αποτέλεσμα" in q:
        sql = """
        SELECT
            outcome,
            COUNT(*) AS conversations
        FROM v_conversations
        GROUP BY outcome
        ORDER BY conversations DESC
        LIMIT 100;
        """
        explanation = "Showing conversation volume by outcome."

    elif "tool" in q or "latency" in q or "εργαλείο" in q:
        sql = """
        SELECT
            tool_name,
            COUNT(*) AS tool_calls,
            ROUND(AVG(latency_ms), 2) AS avg_latency_ms
        FROM v_tool_calls
        GROUP BY tool_name
        ORDER BY tool_calls DESC
        LIMIT 100;
        """
        explanation = "Showing tool call volume and average latency by tool."

    elif "evaluation" in q or "criteria" in q or "κριτήριο" in q:
        sql = """
        SELECT
            criterion_id,
            result,
            COUNT(*) AS conversations
        FROM v_evaluations
        GROUP BY criterion_id, result
        ORDER BY criterion_id, conversations DESC
        LIMIT 200;
        """
        explanation = "Showing evaluation criteria results."

    else:
        sql = """
        SELECT
            start_date,
            COUNT(*) AS conversations
        FROM v_conversations
        GROUP BY start_date
        ORDER BY start_date DESC
        LIMIT 30;
        """
        explanation = "Defaulting to recent daily conversation volume."

    return sql.strip(), explanation