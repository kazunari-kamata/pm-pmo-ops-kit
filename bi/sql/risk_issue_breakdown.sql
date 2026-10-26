WITH parameters AS (
    SELECT CAST(? AS VARCHAR) AS filter_project_id, CAST(? AS DATE) AS start_date, CAST(? AS DATE) AS end_date
),
records AS (
    SELECT
        'リスク' AS record_type,
        fr.project_key AS project_id,
        p.project_name,
        fr.risk_id AS record_id,
        fr.title,
        fr.severity,
        fr.risk_status AS record_status,
        registered_date.calendar_date AS registered_date,
        due_date.calendar_date AS due_date,
        closed_date.calendar_date AS resolved_date
    FROM fact_risk fr
    JOIN dim_project p ON p.project_key = fr.project_key
    JOIN dim_date registered_date ON registered_date.date_key = fr.registered_date_key
    LEFT JOIN dim_date due_date ON due_date.date_key = fr.due_date_key
    LEFT JOIN dim_date closed_date ON closed_date.date_key = fr.closed_date_key
    CROSS JOIN parameters prm
    WHERE (prm.filter_project_id IS NULL OR fr.project_key = prm.filter_project_id)
      AND (prm.end_date IS NULL OR registered_date.calendar_date <= prm.end_date)
      AND (prm.start_date IS NULL OR registered_date.calendar_date >= prm.start_date)
    UNION ALL
    SELECT
        '課題' AS record_type,
        fi.project_key AS project_id,
        p.project_name,
        fi.issue_id AS record_id,
        fi.title,
        fi.severity,
        fi.issue_status AS record_status,
        registered_date.calendar_date AS registered_date,
        due_date.calendar_date AS due_date,
        resolved_date.calendar_date AS resolved_date
    FROM fact_issue fi
    JOIN dim_project p ON p.project_key = fi.project_key
    JOIN dim_date registered_date ON registered_date.date_key = fi.registered_date_key
    LEFT JOIN dim_date due_date ON due_date.date_key = fi.due_date_key
    LEFT JOIN dim_date resolved_date ON resolved_date.date_key = fi.resolved_date_key
    CROSS JOIN parameters prm
    WHERE (prm.filter_project_id IS NULL OR fi.project_key = prm.filter_project_id)
      AND (prm.end_date IS NULL OR registered_date.calendar_date <= prm.end_date)
      AND (prm.start_date IS NULL OR registered_date.calendar_date >= prm.start_date)
)
SELECT * FROM records ORDER BY record_type, severity, registered_date, record_id;
