#!/usr/bin/env python3
"""工程ごとの最小確認項目を出力する。"""

from __future__ import annotations

import argparse


CHECKLISTS = {
    "initiation": [
        "目的、成功指標、対象外をプロジェクト憲章に記録した",
        "スポンサー、PM、主要な関係者と意思決定方法を確認した",
        "初期リスク、前提、制約を登録した",
    ],
    "requirements": [
        "要件ごとに優先度、受入条件、確認者を記録した",
        "対象外と未決事項を明示した",
        "要件と成果物・テストの対応関係を確認した",
        "要件定義の確認者と合意日を記録した",
    ],
    "delivery": [
        "WBS、依存関係、担当、完了条件を更新した",
        "RAIDと変更要求の影響・期限・担当を確認した",
        "進捗差異と対処案、判断依頼を関係者に共有した",
        "レビュー結果と未解決指摘を管理した",
    ],
    "closure": [
        "受入結果、残課題、運用引継ぎを確認した",
        "完了報告の承認者と承認条件を記録した",
        "振り返りのアクションと共有する学びを整理した",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=CHECKLISTS, help="対象工程")
    args = parser.parse_args()

    print(f"# {args.phase} checklist")
    for item in CHECKLISTS[args.phase]:
        print(f"- [ ] {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
