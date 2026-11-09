from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from bi.etl.quality import DataQualityError, validate_sources

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "bi" / "data" / "source"


def test_validate_sources_normalizes_types() -> None:
    data = validate_sources(SOURCE_DIR)

    row = data["wbs_progress.csv"][0]
    assert row["snapshot_date"].isoformat() == "2026-05-31"
    assert str(row["planned_effort_hours"]) == "120"
    assert row["is_blocked"] is False


def test_validate_sources_rejects_duplicate_key(tmp_path: Path) -> None:
    copied_source = tmp_path / "source"
    shutil.copytree(SOURCE_DIR, copied_source)
    progress = copied_source / "wbs_progress.csv"
    original = progress.read_text(encoding="utf-8")
    first_data_row = original.splitlines()[1]
    progress.write_text(f"{original}{first_data_row}\n", encoding="utf-8")

    with pytest.raises(DataQualityError, match="一意キーが重複"):
        validate_sources(copied_source)


def test_validate_sources_rejects_unknown_project(tmp_path: Path) -> None:
    copied_source = tmp_path / "source"
    shutil.copytree(SOURCE_DIR, copied_source)
    issues = copied_source / "issues.csv"
    issues.write_text(
        issues.read_text(encoding="utf-8").replace("ISS-001,PJ-001", "ISS-001,PJ-999"),
        encoding="utf-8",
    )

    with pytest.raises(DataQualityError, match="projects.csv にありません"):
        validate_sources(copied_source)


def test_validate_sources_requires_one_rate_for_each_effort_date(tmp_path: Path) -> None:
    copied_source = tmp_path / "source"
    shutil.copytree(SOURCE_DIR, copied_source)
    rates = copied_source / "resource_rates.csv"
    rates.write_text(
        rates.read_text(encoding="utf-8").replace(
            "RES-003,2026-01-01,,7000,7000,JPY",
            "RES-003,2026-01-01,2026-04-30,7000,7000,JPY",
        ),
        encoding="utf-8",
    )

    with pytest.raises(DataQualityError, match="適用できる単価が1件ではありません"):
        validate_sources(copied_source)
