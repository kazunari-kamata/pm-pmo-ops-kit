WITH input_parameters AS (
    SELECT
        CAST(? AS VARCHAR) AS filter_project_id,
        CAST(? AS DATE) AS start_date,
        CAST(? AS DATE) AS end_date
),
parameters AS (
    SELECT
        input_parameters.*,
        COALESCE(
            end_date,
            (SELECT MAX(d.calendar_date)
             FROM fact_progress fp
             JOIN dim_date d ON d.date_key = fp.snapshot_date_key)
        ) AS as_of_date
    FROM input_parameters
),
selected_projects AS (
    SELECT p.*, prm.start_date, prm.as_of_date
    FROM dim_project p
    CROSS JOIN parameters prm
    WHERE prm.filter_project_id IS NULL OR p.project_key = prm.filter_project_id
),
latest_progress AS (
    SELECT fp.*, snapshot_date.calendar_date AS snapshot_date,
           planned_end_date.calendar_date AS planned_end_date,
           actual_end_date.calendar_date AS actual_end_date,
           prm.as_of_date
    FROM fact_progress fp
    JOIN dim_date snapshot_date ON snapshot_date.date_key = fp.snapshot_date_key
    JOIN dim_date planned_end_date ON planned_end_date.date_key = fp.planned_end_date_key
    LEFT JOIN dim_date actual_end_date ON actual_end_date.date_key = fp.actual_end_date_key
    CROSS JOIN parameters prm
    WHERE snapshot_date.calendar_date <= prm.as_of_date
      AND (prm.filter_project_id IS NULL OR fp.project_key = prm.filter_project_id)
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY fp.project_key, fp.wbs_id ORDER BY snapshot_date.calendar_date DESC
    ) = 1
),
progress_metrics AS (
    SELECT
        project_key,
        ROUND(100.0 * COUNT(*) FILTER (WHERE task_status = '完了') / NULLIF(COUNT(*), 0), 1)
            AS progress_rate_pct,
        ROUND(AVG(CASE
            WHEN actual_end_date IS NOT NULL THEN date_diff('day', planned_end_date, actual_end_date)
            WHEN planned_end_date < as_of_date THEN date_diff('day', planned_end_date, as_of_date)
            ELSE 0
        END), 1) AS schedule_variance_days,
        COUNT(*) FILTER (
            WHERE task_status <> '完了' AND planned_end_date < as_of_date
        ) AS overdue_task_count,
        COUNT(*) FILTER (WHERE is_blocked) AS blocked_task_count
    FROM latest_progress
    GROUP BY project_key
),
milestone_metrics AS (
    SELECT
        fm.project_key,
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE actual_date.calendar_date <= planned_date.calendar_date)
            / NULLIF(COUNT(*), 0),
            1
        ) AS milestone_achievement_rate_pct
    FROM fact_milestone fm
    JOIN dim_date planned_date ON planned_date.date_key = fm.planned_date_key
    LEFT JOIN dim_date actual_date ON actual_date.date_key = fm.actual_date_key
    CROSS JOIN parameters prm
    WHERE planned_date.calendar_date <= prm.as_of_date
      AND (prm.filter_project_id IS NULL OR fm.project_key = prm.filter_project_id)
    GROUP BY fm.project_key
),
issue_metrics AS (
    SELECT
        fi.project_key,
        COUNT(*) FILTER (WHERE fi.issue_status IN ('オープン', '対応中')) AS unresolved_issue_count,
        ROUND(AVG(date_diff('day', registered_date.calendar_date, resolved_date.calendar_date))
              FILTER (WHERE resolved_date.calendar_date <= prm.as_of_date), 1)
            AS average_issue_resolution_days
    FROM fact_issue fi
    JOIN dim_date registered_date ON registered_date.date_key = fi.registered_date_key
    LEFT JOIN dim_date resolved_date ON resolved_date.date_key = fi.resolved_date_key
    CROSS JOIN parameters prm
    WHERE registered_date.calendar_date <= prm.as_of_date
      AND (prm.filter_project_id IS NULL OR fi.project_key = prm.filter_project_id)
    GROUP BY fi.project_key
),
risk_metrics AS (
    SELECT
        fr.project_key,
        COUNT(*) FILTER (
            WHERE fr.severity = '高' AND fr.risk_status IN ('オープン', '対応中')
        ) AS high_risk_count
    FROM fact_risk fr
    JOIN dim_date registered_date ON registered_date.date_key = fr.registered_date_key
    CROSS JOIN parameters prm
    WHERE registered_date.calendar_date <= prm.as_of_date
      AND (prm.filter_project_id IS NULL OR fr.project_key = prm.filter_project_id)
    GROUP BY fr.project_key
),
budget_metrics AS (
    SELECT
        fb.project_key,
        SUM(fb.planned_amount) AS planned_budget_amount,
        SUM(fb.actual_amount) AS actual_budget_amount,
        SUM(fb.forecast_amount) AS forecast_budget_amount
    FROM fact_budget fb
    JOIN dim_date budget_month ON budget_month.date_key = fb.budget_month_date_key
    CROSS JOIN parameters prm
    WHERE budget_month.calendar_date <= prm.as_of_date
      AND (prm.start_date IS NULL OR budget_month.calendar_date >= prm.start_date)
      AND (prm.filter_project_id IS NULL OR fb.project_key = prm.filter_project_id)
    GROUP BY fb.project_key
),
effort_metrics AS (
    SELECT
        fe.project_key,
        SUM(fe.planned_hours) AS planned_effort_hours,
        SUM(fe.actual_hours) AS actual_effort_hours,
        SUM(fe.planned_labor_cost) AS planned_labor_cost,
        SUM(fe.actual_labor_cost) AS actual_labor_cost
    FROM fact_effort fe
    JOIN dim_date work_date ON work_date.date_key = fe.work_date_key
    CROSS JOIN parameters prm
    WHERE work_date.calendar_date <= prm.as_of_date
      AND (prm.start_date IS NULL OR work_date.calendar_date >= prm.start_date)
      AND (prm.filter_project_id IS NULL OR fe.project_key = prm.filter_project_id)
    GROUP BY fe.project_key
),
change_metrics AS (
    SELECT fc.project_key, COUNT(*) FILTER (WHERE fc.change_status = '評価中') AS pending_change_count
    FROM fact_change_request fc
    JOIN dim_date requested_date ON requested_date.date_key = fc.requested_date_key
    CROSS JOIN parameters prm
    WHERE requested_date.calendar_date <= prm.as_of_date
      AND (prm.filter_project_id IS NULL OR fc.project_key = prm.filter_project_id)
    GROUP BY fc.project_key
)
SELECT
    sp.project_key AS project_id,
    sp.project_name,
    sp.portfolio,
    sp.project_status,
    sp.as_of_date,
    pm.progress_rate_pct,
    pm.schedule_variance_days,
    COALESCE(pm.overdue_task_count, 0) AS overdue_task_count,
    COALESCE(pm.blocked_task_count, 0) AS blocked_task_count,
    mm.milestone_achievement_rate_pct,
    COALESCE(im.unresolved_issue_count, 0) AS unresolved_issue_count,
    im.average_issue_resolution_days,
    COALESCE(rm.high_risk_count, 0) AS high_risk_count,
    bm.planned_budget_amount,
    bm.actual_budget_amount,
    bm.forecast_budget_amount,
    ROUND(100.0 * bm.actual_budget_amount / NULLIF(bm.planned_budget_amount, 0), 1)
        AS budget_consumption_rate_pct,
    GREATEST(COALESCE(bm.actual_budget_amount, 0) - COALESCE(bm.planned_budget_amount, 0), 0)
        AS budget_overrun_amount,
    em.planned_effort_hours,
    em.actual_effort_hours,
    ROUND(100.0 * em.actual_effort_hours / NULLIF(em.planned_effort_hours, 0), 1)
        AS effort_actual_vs_plan_rate_pct,
    em.planned_labor_cost,
    em.actual_labor_cost,
    ROUND(100.0 * em.actual_labor_cost / NULLIF(em.planned_labor_cost, 0), 1)
        AS labor_cost_actual_vs_plan_rate_pct,
    COALESCE(cm.pending_change_count, 0) AS pending_change_count
FROM selected_projects sp
LEFT JOIN progress_metrics pm ON pm.project_key = sp.project_key
LEFT JOIN milestone_metrics mm ON mm.project_key = sp.project_key
LEFT JOIN issue_metrics im ON im.project_key = sp.project_key
LEFT JOIN risk_metrics rm ON rm.project_key = sp.project_key
LEFT JOIN budget_metrics bm ON bm.project_key = sp.project_key
LEFT JOIN effort_metrics em ON em.project_key = sp.project_key
LEFT JOIN change_metrics cm ON cm.project_key = sp.project_key
ORDER BY sp.project_key;
