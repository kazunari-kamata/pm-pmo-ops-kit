"""固定SQLファイルを安全なバインド変数付きで実行するための窓口。"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import duckdb

ROOT = Path(__file__).resolve().parents[2]
SQL_DIRECTORY = ROOT / "bi" / "sql"
DEFAULT_DATABASE_PATH = ROOT / "bi" / "data" / "pm_pmo_analytics.duckdb"

SQL_FILES = {
    "kpi_by_project": "kpi_by_project.sql",
    "monthly_budget_effort": "monthly_budget_effort.sql",
    "risk_issue_breakdown": "risk_issue_breakdown.sql",
    "task_details": "task_details.sql",
    "milestone_details": "milestone_details.sql",
    "resource_effort": "resource_effort.sql",
}


def _read_sql(query_name: str) -> str:
    try:
        filename = SQL_FILES[query_name]
    except KeyError as error:
        raise ValueError(f"未定義の分析SQLです: {query_name}") from error
    return (SQL_DIRECTORY / filename).read_text(encoding="utf-8")


def _to_records(result: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def query_records(
    database_path: Path,
    query_name: str,
    project_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    """許可済みSQLと値のバインドだけで分析結果を返す。"""

    with duckdb.connect(str(database_path), read_only=True) as connection:
        result = connection.execute(_read_sql(query_name), [project_id, start_date, end_date])
        return _to_records(result)


def project_options(database_path: Path) -> list[dict[str, str]]:
    with duckdb.connect(str(database_path), read_only=True) as connection:
        result = connection.execute(
            "SELECT project_key AS project_id, project_name FROM dim_project ORDER BY project_key"
        )
        return _to_records(result)


def reporting_date_range(database_path: Path) -> tuple[date, date] | None:
    """入力済みのスナップショットを既定の分析対象期間として返す。"""

    with duckdb.connect(str(database_path), read_only=True) as connection:
        row = connection.execute(
            """
            SELECT MIN(d.calendar_date), MAX(d.calendar_date)
            FROM fact_progress fp
            JOIN dim_date d ON d.date_key = fp.snapshot_date_key
            """
        ).fetchone()
    if row is None or row[0] is None or row[1] is None:
        return None
    return row[0], row[1]
