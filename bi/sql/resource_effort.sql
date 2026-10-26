WITH parameters AS (
    SELECT CAST(? AS VARCHAR) AS filter_project_id, CAST(? AS DATE) AS start_date, CAST(? AS DATE) AS end_date
)
SELECT
    fe.project_key AS project_id,
    p.project_name,
    r.resource_name,
    r.role,
    SUM(fe.planned_hours) AS planned_effort_hours,
    SUM(fe.actual_hours) AS actual_effort_hours,
    ROUND(SUM(fe.planned_labor_cost) / NULLIF(SUM(fe.planned_hours), 0), 2)
        AS planned_hourly_rate,
    ROUND(SUM(fe.actual_labor_cost) / NULLIF(SUM(fe.actual_hours), 0), 2)
        AS actual_hourly_rate,
    SUM(fe.planned_labor_cost) AS planned_labor_cost,
    SUM(fe.actual_labor_cost) AS actual_labor_cost
FROM fact_effort fe
JOIN dim_project p ON p.project_key = fe.project_key
JOIN dim_resource r ON r.resource_key = fe.resource_key
JOIN dim_date work_date ON work_date.date_key = fe.work_date_key
CROSS JOIN parameters prm
WHERE (prm.filter_project_id IS NULL OR fe.project_key = prm.filter_project_id)
  AND (prm.start_date IS NULL OR work_date.calendar_date >= prm.start_date)
  AND (prm.end_date IS NULL OR work_date.calendar_date <= prm.end_date)
GROUP BY fe.project_key, p.project_name, r.resource_name, r.role
ORDER BY project_id, resource_name;
