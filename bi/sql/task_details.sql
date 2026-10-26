WITH parameters AS (
    SELECT CAST(? AS VARCHAR) AS filter_project_id, CAST(? AS DATE) AS start_date, CAST(? AS DATE) AS end_date
),
latest_tasks AS (
    SELECT
        fp.project_key AS project_id,
        p.project_name,
        fp.wbs_id,
        fp.task_name,
        fp.task_status,
        fp.planned_progress_pct,
        fp.actual_progress_pct,
        fp.is_blocked,
        planned_end_date.calendar_date AS planned_end_date,
        actual_end_date.calendar_date AS actual_end_date,
        snapshot_date.calendar_date AS snapshot_date,
        prm.end_date
    FROM fact_progress fp
    JOIN dim_project p ON p.project_key = fp.project_key
    JOIN dim_date snapshot_date ON snapshot_date.date_key = fp.snapshot_date_key
    JOIN dim_date planned_end_date ON planned_end_date.date_key = fp.planned_end_date_key
    LEFT JOIN dim_date actual_end_date ON actual_end_date.date_key = fp.actual_end_date_key
    CROSS JOIN parameters prm
    WHERE (prm.filter_project_id IS NULL OR fp.project_key = prm.filter_project_id)
      AND (prm.end_date IS NULL OR snapshot_date.calendar_date <= prm.end_date)
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY fp.project_key, fp.wbs_id ORDER BY snapshot_date.calendar_date DESC
    ) = 1
)
SELECT *,
       CASE WHEN task_status <> '完了' AND planned_end_date < COALESCE(end_date, snapshot_date)
            THEN TRUE ELSE FALSE END AS is_overdue
FROM latest_tasks
ORDER BY is_overdue DESC, planned_end_date, project_id, wbs_id;
