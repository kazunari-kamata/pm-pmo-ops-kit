WITH parameters AS (
    SELECT CAST(? AS VARCHAR) AS filter_project_id, CAST(? AS DATE) AS start_date, CAST(? AS DATE) AS end_date
)
SELECT
    fm.project_key AS project_id,
    p.project_name,
    fm.milestone_id,
    fm.milestone_name,
    planned_date.calendar_date AS planned_date,
    actual_date.calendar_date AS actual_date,
    fm.milestone_status,
    CASE
        WHEN actual_date.calendar_date <= planned_date.calendar_date THEN '期限内完了'
        WHEN actual_date.calendar_date > planned_date.calendar_date THEN '遅延完了'
        WHEN planned_date.calendar_date < COALESCE(prm.end_date, planned_date.calendar_date) THEN '期限超過'
        ELSE '予定前'
    END AS achievement_status
FROM fact_milestone fm
JOIN dim_project p ON p.project_key = fm.project_key
JOIN dim_date planned_date ON planned_date.date_key = fm.planned_date_key
LEFT JOIN dim_date actual_date ON actual_date.date_key = fm.actual_date_key
CROSS JOIN parameters prm
WHERE (prm.filter_project_id IS NULL OR fm.project_key = prm.filter_project_id)
  AND (prm.start_date IS NULL OR planned_date.calendar_date >= prm.start_date)
  AND (prm.end_date IS NULL OR planned_date.calendar_date <= prm.end_date)
ORDER BY planned_date, project_id, milestone_id;
