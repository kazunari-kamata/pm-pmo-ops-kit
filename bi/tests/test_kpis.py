from __future__ import annotations

from pathlib import Path

import pytest

from bi.app.queries import query_records
from bi.etl.pipeline import build_database

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "bi" / "data" / "source"


@pytest.fixture()
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "analytics.duckdb"
    build_database(SOURCE_DIR, path)
    return path


def test_kpis_match_source_data_without_double_counting(database_path: Path) -> None:
    rows = query_records(database_path, "kpi_by_project")
    pj001 = next(row for row in rows if row["project_id"] == "PJ-001")

    assert pj001["progress_rate_pct"] == 33.3
    assert pj001["schedule_variance_days"] == 6.7
    assert pj001["milestone_achievement_rate_pct"] == 0.0
    assert pj001["overdue_task_count"] == 1
    assert pj001["unresolved_issue_count"] == 1
    assert pj001["average_issue_resolution_days"] == 12.0
    assert pj001["high_risk_count"] == 1
    assert float(pj001["planned_budget_amount"]) == 950000
    assert float(pj001["actual_budget_amount"]) == 970000
    assert pj001["budget_consumption_rate_pct"] == 102.1
    assert float(pj001["budget_overrun_amount"]) == 20000
    assert pj001["effort_actual_vs_plan_rate_pct"] == 105.8
    assert float(pj001["planned_labor_cost"]) == 1960000
    assert float(pj001["actual_labor_cost"]) == 2076800
    assert pj001["labor_cost_actual_vs_plan_rate_pct"] == 106.0


def test_project_filter_is_bound_as_a_value(database_path: Path) -> None:
    suspicious_value = "PJ-001' OR 1=1 --"

    assert query_records(database_path, "kpi_by_project", project_id=suspicious_value) == []
    assert len(query_records(database_path, "kpi_by_project")) == 3
