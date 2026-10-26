"""架空CSVからDuckDBの分析データベースを生成するCLI。"""

from __future__ import annotations

import argparse
from pathlib import Path

from bi.etl.pipeline import build_database
from bi.etl.quality import DataQualityError

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = ROOT / "bi" / "data" / "source"
DEFAULT_DATABASE_PATH = ROOT / "bi" / "data" / "pm_pmo_analytics.duckdb"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="入力CSVのディレクトリ"
    )
    parser.add_argument(
        "--database", type=Path, default=DEFAULT_DATABASE_PATH, help="出力DuckDBファイル"
    )
    args = parser.parse_args()
    try:
        counts = build_database(args.source_dir, args.database)
    except DataQualityError as error:
        print(f"データ品質エラー: {error}")
        return 1
    total = sum(counts.values())
    print(f"ETL完了: {total}行を {args.database} に格納しました")
    for filename, count in counts.items():
        print(f"- {filename}: {count}行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
