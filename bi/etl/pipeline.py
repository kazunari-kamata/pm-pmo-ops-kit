"""検証済みCSVをスタースキーマへ変換してDuckDBファイルを作成する。"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import duckdb

from bi.etl.quality import validate_sources
from bi.models.star_schema import CREATE_STATEMENTS, DROP_STATEMENTS

NormalizedData = dict[str, list[dict[str, Any]]]


def _date_key(value: date | None) -> int | None:
    return int(value.strftime("%Y%m%d")) if value else None


def _resource_rate_key(rate: dict[str, Any]) -> str:
    return f"{rate['resource_id']}:{rate['effective_start_date'].strftime('%Y%m%d')}"


def _rate_for_effort(
    effort: dict[str, Any], rates_by_resource: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    matching_rates = [
        rate
        for rate in rates_by_resource[effort["resource_id"]]
        if rate["effective_start_date"] <= effort["work_date"]
        and (
            rate["effective_end_date"] is None or effort["work_date"] <= rate["effective_end_date"]
        )
    ]
    return matching_rates[0]


def _labor_cost(hours: Decimal, hourly_rate: Decimal) -> Decimal:
    return (hours * hourly_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _all_dates(data: NormalizedData) -> list[date]:
    dates = {
        value
        for rows in data.values()
        for row in rows
        for value in row.values()
        if isinstance(value, date)
    }
    return sorted(dates)


def _insert_rows(
    connection: duckdb.DuckDBPyConnection,
    statement: str,
    rows: Iterable[tuple[Any, ...]],
) -> None:
    values = list(rows)
    if values:
        connection.executemany(statement, values)


def _create_schema(connection: duckdb.DuckDBPyConnection) -> None:
    for statement in DROP_STATEMENTS:
        connection.execute(statement)
    for statement in CREATE_STATEMENTS:
        connection.execute(statement)


def _load_dimensions(connection: duckdb.DuckDBPyConnection, data: NormalizedData) -> None:
    _insert_rows(
        connection,
        """INSERT INTO dim_project VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            (
                row["project_id"],
                row["project_name"],
                row["portfolio"],
                row["status"],
                row["planned_start_date"],
                row["planned_end_date"],
                row["actual_start_date"],
                row["actual_end_date"],
                row["project_manager"],
            )
            for row in data["projects.csv"]
        ),
    )
    _insert_rows(
        connection,
        """INSERT INTO dim_date VALUES (?, ?, ?, ?, ?)""",
        (
            (_date_key(value), value, value.year, value.month, value.strftime("%Y-%m"))
            for value in _all_dates(data)
        ),
    )
    _insert_rows(
        connection,
        """INSERT INTO dim_resource VALUES (?, ?, ?)""",
        ((row["resource_id"], row["resource_name"], row["role"]) for row in data["resources.csv"]),
    )
    _insert_rows(
        connection,
        """INSERT INTO dim_resource_rate VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            (
                _resource_rate_key(row),
                row["resource_id"],
                _date_key(row["effective_start_date"]),
                _date_key(row["effective_end_date"]),
                row["planned_hourly_rate"],
                row["actual_hourly_rate"],
                row["currency"],
            )
            for row in data["resource_rates.csv"]
        ),
    )


def _load_facts(connection: duckdb.DuckDBPyConnection, data: NormalizedData) -> None:
    _insert_rows(
        connection,
        """INSERT INTO fact_progress VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            (
                row["project_id"],
                row["wbs_id"],
                row["task_name"],
                _date_key(row["snapshot_date"]),
                _date_key(row["planned_start_date"]),
                _date_key(row["planned_end_date"]),
                _date_key(row["actual_start_date"]),
                _date_key(row["actual_end_date"]),
                row["status"],
                row["planned_progress_pct"],
                row["actual_progress_pct"],
                row["planned_effort_hours"],
                row["actual_effort_hours"],
                row["is_blocked"],
            )
            for row in data["wbs_progress.csv"]
        ),
    )
    _insert_rows(
        connection,
        """INSERT INTO fact_milestone VALUES (?, ?, ?, ?, ?, ?)""",
        (
            (
                row["project_id"],
                row["milestone_id"],
                row["milestone_name"],
                _date_key(row["planned_date"]),
                _date_key(row["actual_date"]),
                row["status"],
            )
            for row in data["milestones.csv"]
        ),
    )
    _insert_rows(
        connection,
        """INSERT INTO fact_issue VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            (
                row["issue_id"],
                row["project_id"],
                row["title"],
                _date_key(row["registered_date"]),
                _date_key(row["due_date"]),
                _date_key(row["resolved_date"]),
                row["severity"],
                row["status"],
            )
            for row in data["issues.csv"]
        ),
    )
    _insert_rows(
        connection,
        """INSERT INTO fact_risk VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            (
                row["risk_id"],
                row["project_id"],
                row["title"],
                _date_key(row["registered_date"]),
                _date_key(row["due_date"]),
                _date_key(row["closed_date"]),
                row["severity"],
                row["probability"],
                row["impact"],
                row["status"],
            )
            for row in data["risks.csv"]
        ),
    )
    _insert_rows(
        connection,
        """INSERT INTO fact_change_request VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            (
                row["change_id"],
                row["project_id"],
                row["title"],
                _date_key(row["requested_date"]),
                _date_key(row["decision_date"]),
                row["status"],
                row["cost_impact_amount"],
                row["schedule_impact_days"],
            )
            for row in data["change_requests.csv"]
        ),
    )
    _insert_rows(
        connection,
        """INSERT INTO fact_budget VALUES (?, ?, ?, ?, ?, ?)""",
        (
            (
                row["project_id"],
                _date_key(row["budget_month"]),
                row["budget_category"],
                row["planned_amount"],
                row["actual_amount"],
                row["forecast_amount"],
            )
            for row in data["budget.csv"]
        ),
    )
    rates_by_resource: dict[str, list[dict[str, Any]]] = {}
    for rate in data["resource_rates.csv"]:
        rates_by_resource.setdefault(rate["resource_id"], []).append(rate)
    _insert_rows(
        connection,
        """INSERT INTO fact_effort VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            (
                row["project_id"],
                row["resource_id"],
                _resource_rate_key(_rate_for_effort(row, rates_by_resource)),
                _date_key(row["work_date"]),
                row["planned_hours"],
                row["actual_hours"],
                _rate_for_effort(row, rates_by_resource)["planned_hourly_rate"],
                _rate_for_effort(row, rates_by_resource)["actual_hourly_rate"],
                _labor_cost(
                    row["planned_hours"],
                    _rate_for_effort(row, rates_by_resource)["planned_hourly_rate"],
                ),
                _labor_cost(
                    row["actual_hours"],
                    _rate_for_effort(row, rates_by_resource)["actual_hourly_rate"],
                ),
            )
            for row in data["effort.csv"]
        ),
    )


def build_database(source_dir: Path, database_path: Path) -> dict[str, int]:
    """入力検証後、完全な一時DBを原子的に置き換える冪等ETLを実行する。"""

    data = validate_sources(source_dir)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{database_path.stem}-", suffix=".duckdb", dir=database_path.parent
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    temporary_path.unlink()
    try:
        connection = duckdb.connect(str(temporary_path))
        try:
            _create_schema(connection)
            _load_dimensions(connection, data)
            _load_facts(connection, data)
        finally:
            connection.close()
        temporary_path.replace(database_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return {filename: len(rows) for filename, rows in data.items()}
