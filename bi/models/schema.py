"""入力CSVのスキーマ定義。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    """CSV列の型、必須条件、許容値を表す。"""

    name: str
    data_type: str = "string"
    nullable: bool = False
    allowed_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceSchema:
    """1つの入力CSVの列と一意性制約を表す。"""

    filename: str
    columns: tuple[Column, ...]
    unique_key: tuple[str, ...]


SOURCES = (
    SourceSchema(
        "projects.csv",
        (
            Column("project_id"),
            Column("project_name"),
            Column("portfolio"),
            Column("status", allowed_values=("進行中", "完了", "保留")),
            Column("planned_start_date", "date"),
            Column("planned_end_date", "date"),
            Column("actual_start_date", "date", nullable=True),
            Column("actual_end_date", "date", nullable=True),
            Column("project_manager"),
        ),
        ("project_id",),
    ),
    SourceSchema(
        "resources.csv",
        (Column("resource_id"), Column("resource_name"), Column("role")),
        ("resource_id",),
    ),
    SourceSchema(
        "resource_rates.csv",
        (
            Column("resource_id"),
            Column("effective_start_date", "date"),
            Column("effective_end_date", "date", nullable=True),
            Column("planned_hourly_rate", "decimal"),
            Column("actual_hourly_rate", "decimal"),
            Column("currency", allowed_values=("JPY",)),
        ),
        ("resource_id", "effective_start_date"),
    ),
    SourceSchema(
        "wbs_progress.csv",
        (
            Column("project_id"),
            Column("wbs_id"),
            Column("task_name"),
            Column("snapshot_date", "date"),
            Column("planned_start_date", "date"),
            Column("planned_end_date", "date"),
            Column("actual_start_date", "date", nullable=True),
            Column("actual_end_date", "date", nullable=True),
            Column("status", allowed_values=("未着手", "進行中", "完了", "保留")),
            Column("planned_progress_pct", "decimal"),
            Column("actual_progress_pct", "decimal"),
            Column("planned_effort_hours", "decimal"),
            Column("actual_effort_hours", "decimal"),
            Column("is_blocked", "boolean"),
        ),
        ("project_id", "wbs_id", "snapshot_date"),
    ),
    SourceSchema(
        "milestones.csv",
        (
            Column("project_id"),
            Column("milestone_id"),
            Column("milestone_name"),
            Column("planned_date", "date"),
            Column("actual_date", "date", nullable=True),
            Column("status", allowed_values=("未着手", "進行中", "完了", "保留")),
        ),
        ("project_id", "milestone_id"),
    ),
    SourceSchema(
        "risks.csv",
        (
            Column("risk_id"),
            Column("project_id"),
            Column("title"),
            Column("registered_date", "date"),
            Column("due_date", "date", nullable=True),
            Column("closed_date", "date", nullable=True),
            Column("severity", allowed_values=("高", "中", "低")),
            Column("probability", allowed_values=("高", "中", "低")),
            Column("impact"),
            Column("status", allowed_values=("オープン", "対応中", "解決済み", "受容")),
        ),
        ("risk_id",),
    ),
    SourceSchema(
        "issues.csv",
        (
            Column("issue_id"),
            Column("project_id"),
            Column("title"),
            Column("registered_date", "date"),
            Column("due_date", "date", nullable=True),
            Column("resolved_date", "date", nullable=True),
            Column("severity", allowed_values=("高", "中", "低")),
            Column("status", allowed_values=("オープン", "対応中", "解決済み")),
        ),
        ("issue_id",),
    ),
    SourceSchema(
        "change_requests.csv",
        (
            Column("change_id"),
            Column("project_id"),
            Column("title"),
            Column("requested_date", "date"),
            Column("decision_date", "date", nullable=True),
            Column("status", allowed_values=("評価中", "承認済み", "却下", "撤回")),
            Column("cost_impact_amount", "decimal"),
            Column("schedule_impact_days", "integer"),
        ),
        ("change_id",),
    ),
    SourceSchema(
        "budget.csv",
        (
            Column("project_id"),
            Column("budget_month", "date"),
            Column("budget_category"),
            Column("planned_amount", "decimal"),
            Column("actual_amount", "decimal"),
            Column("forecast_amount", "decimal"),
        ),
        ("project_id", "budget_month", "budget_category"),
    ),
    SourceSchema(
        "effort.csv",
        (
            Column("project_id"),
            Column("resource_id"),
            Column("work_date", "date"),
            Column("planned_hours", "decimal"),
            Column("actual_hours", "decimal"),
        ),
        ("project_id", "resource_id", "work_date"),
    ),
)

SOURCE_BY_FILENAME = {source.filename: source for source in SOURCES}
