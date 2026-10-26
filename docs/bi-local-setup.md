# BIローカル環境構築手順

## 前提

- Python 3.12以降
- リポジトリルートでコマンドを実行できること
- 外部サービスへの登録は不要

## セットアップ

```sh
python -m pip install -e ".[bi,dev]"
python -m bi.etl.run
python -m streamlit run bi/app/dashboard.py
```

最初のコマンドはDuckDB、Streamlit、Plotly、pytest、Ruffを導入します。2つ目のコマンドで架空CSVを検証して分析データベースを生成します。3つ目のコマンドでダッシュボードを起動します。

## 検証

```sh
python -m pytest
ruff check .
ruff format --check .
python scripts/validate_templates.py templates
python scripts/generate_project_checklist.py requirements
python scripts/generate_project_checklist.py closure
```

## よくある確認

| 状況 | 確認・対処 |
| --- | --- |
| ETLが入力エラーで停止した | エラーメッセージのファイル・行・列を確認し、`docs/bi-data-quality-rules.md`に従ってCSVを修正する |
| ダッシュボードが分析DB未作成と表示する | `python -m bi.etl.run`を実行する |
| 画面が空になる | プロジェクト・期間の絞り込み条件を見直す。該当データがない場合は正常な表示である |
| CSVを更新したのに画面へ反映されない | ETLを再実行し、画面を更新する |
