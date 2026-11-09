WITH parameters AS (
    SELECT CAST(? AS VARCHAR) AS filter_project_id, CAST(? AS DATE) AS start_date, CAST(? AS DATE) AS end_date
),
budget_monthly AS (
    SELECT
        fb.project_key,
        budget_date.calendar_date AS month_date,
        SUM(fb.planned_amount) AS planned_budget_amount,
        SUM(fb.actual_amount) AS actual_budget_amount,
        SUM(fb.forecast_amount) AS forecast_budget_amount
    FROM fact_budget fb
    JOIN dim_date budget_date ON budget_date.date_key = fb.budget_month_date_key
    CROSS JOIN parameters prm
    WHERE (prm.filter_project_id IS NULL OR fb.project_key = prm.filter_project_id)
      AND (prm.start_date IS NULL OR budget_date.calendar_date >= prm.start_date)
      AND (prm.end_date IS NULL OR budget_date.calendar_date <= prm.end_date)
    GROUP BY fb.project_key, budget_date.calendar_date
),
effort_monthly AS (
    SELECT
        fe.project_key,
        date_trunc('month', work_date.calendar_date)::DATE AS month_date,
        SUM(fe.planned_hours) AS planned_effort_hours,
        SUM(fe.actual_hours) AS actual_effort_hours,
        SUM(fe.planned_labor_cost) AS planned_labor_cost,
        SUM(fe.actual_labor_cost) AS actual_labor_cost
    FROM fact_effort fe
    JOIN dim_date work_date ON work_date.date_key = fe.work_date_key
    CROSS JOIN parameters prm
    WHERE (prm.filter_project_id IS NULL OR fe.project_key = prm.filter_project_id)
      AND (prm.start_date IS NULL OR work_date.calendar_date >= prm.start_date)
      AND (prm.end_date IS NULL OR work_date.calendar_date <= prm.end_date)
    GROUP BY fe.project_key, date_trunc('month', work_date.calendar_date)::DATE
)
SELECT
    COALESCE(b.project_key, e.project_key) AS project_id,
    p.project_name,
    COALESCE(b.month_date, e.month_date) AS month_date,
    COALESCE(b.planned_budget_amount, 0) AS planned_budget_amount,
    COALESCE(b.actual_budget_amount, 0) AS actual_budget_amount,
    COALESCE(b.forecast_budget_amount, 0) AS forecast_budget_amount,
    COALESCE(e.planned_effort_hours, 0) AS planned_effort_hours,
    COALESCE(e.actual_effort_hours, 0) AS actual_effort_hours,
    COALESCE(e.planned_labor_cost, 0) AS planned_labor_cost,
    COALESCE(e.actual_labor_cost, 0) AS actual_labor_cost
FROM budget_monthly b
FULL OUTER JOIN effort_monthly e ON b.project_key = e.project_key AND b.month_date = e.month_date
JOIN dim_project p ON p.project_key = COALESCE(b.project_key, e.project_key)
ORDER BY month_date, project_id;
