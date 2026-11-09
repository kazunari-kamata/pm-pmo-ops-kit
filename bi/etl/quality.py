"""入力CSVのスキーマ・値・参照整合性を検証し、型を正規化する。"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from bi.models.schema import SOURCES, Column, SourceSchema


class DataQualityError(ValueError):
    """ETLを停止すべき入力データ品質エラー。"""


def _parse_value(value: str, column: Column, filename: str, row_number: int) -> Any:
    if value == "":
        if column.nullable:
            return None
        raise DataQualityError(f"{filename}:{row_number}: {column.name} は必須です")
    try:
        if column.data_type == "date":
            return date.fromisoformat(value)
        if column.data_type == "decimal":
            return Decimal(value)
        if column.data_type == "integer":
            return int(value)
        if column.data_type == "boolean":
            if value not in {"true", "false"}:
                raise ValueError("true または false で指定してください")
            return value == "true"
    except (ValueError, InvalidOperation) as error:
        raise DataQualityError(
            f"{filename}:{row_number}: {column.name} の形式が不正です: {value}"
        ) from error
    if column.allowed_values and value not in column.allowed_values:
        allowed = "、".join(column.allowed_values)
        raise DataQualityError(
            f"{filename}:{row_number}: {column.name} は {allowed} のいずれかです"
        )
    return value


def _validate_header(fieldnames: list[str] | None, schema: SourceSchema) -> None:
    actual = set(fieldnames or [])
    expected = {column.name for column in schema.columns}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"不足列: {', '.join(missing)}")
        if unexpected:
            details.append(f"未定義列: {', '.join(unexpected)}")
        raise DataQualityError(f"{schema.filename}: ヘッダーが不正です（{' / '.join(details)}）")


def _validate_row_rules(filename: str, row_number: int, row: dict[str, Any]) -> None:
    for key, value in row.items():
        if (
            key.endswith("_amount")
            or key.endswith("_hours")
            or key.endswith("_pct")
            or key.endswith("_hourly_rate")
        ):
            if value is not None and value < 0:
                raise DataQualityError(f"{filename}:{row_number}: {key} は0以上で指定してください")
    for key in ("planned_progress_pct", "actual_progress_pct"):
        if key in row and row[key] > 100:
            raise DataQualityError(f"{filename}:{row_number}: {key} は100以下で指定してください")
    if "schedule_impact_days" in row and row["schedule_impact_days"] < 0:
        raise DataQualityError(
            f"{filename}:{row_number}: schedule_impact_days は0以上で指定してください"
        )
    for start_key, end_key in (
        ("planned_start_date", "planned_end_date"),
        ("actual_start_date", "actual_end_date"),
        ("effective_start_date", "effective_end_date"),
    ):
        has_invalid_date_order = (
            start_key in row
            and row.get(start_key)
            and row.get(end_key)
            and row[start_key] > row[end_key]
        )
        if has_invalid_date_order:
            raise DataQualityError(
                f"{filename}:{row_number}: {start_key} は {end_key} 以前で指定してください"
            )


def _read_source(source_dir: Path, schema: SourceSchema) -> list[dict[str, Any]]:
    path = source_dir / schema.filename
    if not path.is_file():
        raise DataQualityError(f"入力ファイルがありません: {schema.filename}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_header(reader.fieldnames, schema)
        rows: list[dict[str, Any]] = []
        seen_keys: set[tuple[Any, ...]] = set()
        for row_number, raw_row in enumerate(reader, start=2):
            if None in raw_row or any(value is None for value in raw_row.values()):
                raise DataQualityError(f"{schema.filename}:{row_number}: 列数が不正です")
            row = {
                column.name: _parse_value(
                    raw_row[column.name].strip(), column, schema.filename, row_number
                )
                for column in schema.columns
            }
            _validate_row_rules(schema.filename, row_number, row)
            unique_key = tuple(row[key] for key in schema.unique_key)
            if unique_key in seen_keys:
                joined_key = ", ".join(str(value) for value in unique_key)
                raise DataQualityError(
                    f"{schema.filename}:{row_number}: 一意キーが重複しています: {joined_key}"
                )
            seen_keys.add(unique_key)
            rows.append(row)
    return rows


def _validate_references(data: dict[str, list[dict[str, Any]]]) -> None:
    project_ids = {row["project_id"] for row in data["projects.csv"]}
    resource_ids = {row["resource_id"] for row in data["resources.csv"]}
    for filename, rows in data.items():
        if filename in {"projects.csv", "resources.csv", "resource_rates.csv"}:
            continue
        for row_number, row in enumerate(rows, start=2):
            if row["project_id"] not in project_ids:
                raise DataQualityError(
                    f"{filename}:{row_number}: project_id が projects.csv にありません"
                )
    for row_number, row in enumerate(data["effort.csv"], start=2):
        if row["resource_id"] not in resource_ids:
            raise DataQualityError(
                f"effort.csv:{row_number}: resource_id が resources.csv にありません"
            )
    for row_number, row in enumerate(data["resource_rates.csv"], start=2):
        if row["resource_id"] not in resource_ids:
            raise DataQualityError(
                f"resource_rates.csv:{row_number}: resource_id が resources.csv にありません"
            )
    _validate_rate_periods(data)


def _validate_rate_periods(data: dict[str, list[dict[str, Any]]]) -> None:
    rates_by_resource: dict[str, list[dict[str, Any]]] = {}
    for rate in data["resource_rates.csv"]:
        rates_by_resource.setdefault(rate["resource_id"], []).append(rate)
    for resource_id, rates in rates_by_resource.items():
        ordered_rates = sorted(rates, key=lambda row: row["effective_start_date"])
        for previous, current in zip(ordered_rates, ordered_rates[1:], strict=False):
            previous_end = previous["effective_end_date"]
            if previous_end is None or current["effective_start_date"] <= previous_end:
                raise DataQualityError(
                    f"resource_rates.csv: resource_id {resource_id} の単価適用期間が重複しています"
                )
    for row_number, effort in enumerate(data["effort.csv"], start=2):
        matching_rates = [
            rate
            for rate in rates_by_resource.get(effort["resource_id"], [])
            if rate["effective_start_date"] <= effort["work_date"]
            and (
                rate["effective_end_date"] is None
                or effort["work_date"] <= rate["effective_end_date"]
            )
        ]
        if len(matching_rates) != 1:
            raise DataQualityError(
                f"effort.csv:{row_number}: work_date に適用できる単価が1件ではありません"
            )


def validate_sources(source_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """全入力を検証し、日付・数値・真偽値をPython型へ正規化して返す。"""

    if not source_dir.is_dir():
        raise DataQualityError(f"入力ディレクトリがありません: {source_dir}")
    data = {schema.filename: _read_source(source_dir, schema) for schema in SOURCES}
    _validate_references(data)
    return data
