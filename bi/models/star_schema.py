"""DuckDBに作成する分析用スタースキーマ。"""

from __future__ import annotations

DROP_STATEMENTS = (
    "DROP TABLE IF EXISTS fact_effort",
    "DROP TABLE IF EXISTS fact_budget",
    "DROP TABLE IF EXISTS fact_change_request",
    "DROP TABLE IF EXISTS fact_risk",
    "DROP TABLE IF EXISTS fact_issue",
    "DROP TABLE IF EXISTS fact_milestone",
    "DROP TABLE IF EXISTS fact_progress",
    "DROP TABLE IF EXISTS dim_resource_rate",
    "DROP TABLE IF EXISTS dim_resource",
    "DROP TABLE IF EXISTS dim_date",
    "DROP TABLE IF EXISTS dim_project",
)


CREATE_STATEMENTS = (
    """
    CREATE TABLE dim_project (
        project_key VARCHAR PRIMARY KEY,
        project_name VARCHAR NOT NULL,
        portfolio VARCHAR NOT NULL,
        project_status VARCHAR NOT NULL,
        planned_start_date DATE NOT NULL,
        planned_end_date DATE NOT NULL,
        actual_start_date DATE,
        actual_end_date DATE,
        project_manager VARCHAR NOT NULL
    )
    """,
    """
    CREATE TABLE dim_date (
        date_key INTEGER PRIMARY KEY,
        calendar_date DATE NOT NULL UNIQUE,
        year_number INTEGER NOT NULL,
        month_number INTEGER NOT NULL,
        year_month VARCHAR NOT NULL
    )
    """,
    """
    CREATE TABLE dim_resource (
        resource_key VARCHAR PRIMARY KEY,
        resource_name VARCHAR NOT NULL,
        role VARCHAR NOT NULL
    )
    """,
    """
    CREATE TABLE dim_resource_rate (
        resource_rate_key VARCHAR PRIMARY KEY,
        resource_key VARCHAR NOT NULL REFERENCES dim_resource(resource_key),
        effective_start_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        effective_end_date_key INTEGER REFERENCES dim_date(date_key),
        planned_hourly_rate DECIMAL(14, 2) NOT NULL,
        actual_hourly_rate DECIMAL(14, 2) NOT NULL,
        currency VARCHAR NOT NULL
    )
    """,
    """
    CREATE TABLE fact_progress (
        project_key VARCHAR NOT NULL REFERENCES dim_project(project_key),
        wbs_id VARCHAR NOT NULL,
        task_name VARCHAR NOT NULL,
        snapshot_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        planned_start_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        planned_end_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        actual_start_date_key INTEGER REFERENCES dim_date(date_key),
        actual_end_date_key INTEGER REFERENCES dim_date(date_key),
        task_status VARCHAR NOT NULL,
        planned_progress_pct DECIMAL(7, 2) NOT NULL,
        actual_progress_pct DECIMAL(7, 2) NOT NULL,
        planned_effort_hours DECIMAL(12, 2) NOT NULL,
        actual_effort_hours DECIMAL(12, 2) NOT NULL,
        is_blocked BOOLEAN NOT NULL,
        PRIMARY KEY (project_key, wbs_id, snapshot_date_key)
    )
    """,
    """
    CREATE TABLE fact_milestone (
        project_key VARCHAR NOT NULL REFERENCES dim_project(project_key),
        milestone_id VARCHAR NOT NULL,
        milestone_name VARCHAR NOT NULL,
        planned_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        actual_date_key INTEGER REFERENCES dim_date(date_key),
        milestone_status VARCHAR NOT NULL,
        PRIMARY KEY (project_key, milestone_id)
    )
    """,
    """
    CREATE TABLE fact_issue (
        issue_id VARCHAR PRIMARY KEY,
        project_key VARCHAR NOT NULL REFERENCES dim_project(project_key),
        title VARCHAR NOT NULL,
        registered_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        due_date_key INTEGER REFERENCES dim_date(date_key),
        resolved_date_key INTEGER REFERENCES dim_date(date_key),
        severity VARCHAR NOT NULL,
        issue_status VARCHAR NOT NULL
    )
    """,
    """
    CREATE TABLE fact_risk (
        risk_id VARCHAR PRIMARY KEY,
        project_key VARCHAR NOT NULL REFERENCES dim_project(project_key),
        title VARCHAR NOT NULL,
        registered_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        due_date_key INTEGER REFERENCES dim_date(date_key),
        closed_date_key INTEGER REFERENCES dim_date(date_key),
        severity VARCHAR NOT NULL,
        probability VARCHAR NOT NULL,
        impact VARCHAR NOT NULL,
        risk_status VARCHAR NOT NULL
    )
    """,
    """
    CREATE TABLE fact_change_request (
        change_id VARCHAR PRIMARY KEY,
        project_key VARCHAR NOT NULL REFERENCES dim_project(project_key),
        title VARCHAR NOT NULL,
        requested_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        decision_date_key INTEGER REFERENCES dim_date(date_key),
        change_status VARCHAR NOT NULL,
        cost_impact_amount DECIMAL(14, 2) NOT NULL,
        schedule_impact_days INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE fact_budget (
        project_key VARCHAR NOT NULL REFERENCES dim_project(project_key),
        budget_month_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        budget_category VARCHAR NOT NULL,
        planned_amount DECIMAL(14, 2) NOT NULL,
        actual_amount DECIMAL(14, 2) NOT NULL,
        forecast_amount DECIMAL(14, 2) NOT NULL,
        PRIMARY KEY (project_key, budget_month_date_key, budget_category)
    )
    """,
    """
    CREATE TABLE fact_effort (
        project_key VARCHAR NOT NULL REFERENCES dim_project(project_key),
        resource_key VARCHAR NOT NULL REFERENCES dim_resource(resource_key),
        resource_rate_key VARCHAR NOT NULL REFERENCES dim_resource_rate(resource_rate_key),
        work_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        planned_hours DECIMAL(12, 2) NOT NULL,
        actual_hours DECIMAL(12, 2) NOT NULL,
        planned_hourly_rate DECIMAL(14, 2) NOT NULL,
        actual_hourly_rate DECIMAL(14, 2) NOT NULL,
        planned_labor_cost DECIMAL(16, 2) NOT NULL,
        actual_labor_cost DECIMAL(16, 2) NOT NULL,
        PRIMARY KEY (project_key, resource_key, work_date_key)
    )
    """,
)
