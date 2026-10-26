from __future__ import annotations

from pathlib import Path

import duckdb

from bi.etl.pipeline import build_database

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "bi" / "data" / "source"


def test_build_database_creates_star_schema_and_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "analytics.duckdb"

    first_counts = build_database(SOURCE_DIR, database_path)
    second_counts = build_database(SOURCE_DIR, database_path)

    assert first_counts == second_counts
    with duckdb.connect(str(database_path), read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM dim_project").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM fact_progress").fetchone()[0] == 8
        assert connection.execute("SELECT COUNT(*) FROM fact_budget").fetchone()[0] == 9
        assert connection.execute("SELECT COUNT(*) FROM fact_effort").fetchone()[0] == 9
        assert connection.execute("SELECT COUNT(*) FROM dim_resource_rate").fetchone()[0] == 4
        labor_cost = connection.execute(
            """
            SELECT planned_labor_cost, actual_labor_cost
            FROM fact_effort
            WHERE project_key = 'PJ-001' AND resource_key = 'RES-001'
            """
        ).fetchone()
        assert labor_cost == (640000, 721600)
