# BI ETL設計書

## 入力と出力

入力は`bi/data/source/`のUTF-8 CSVです。ETLの出力は`bi/data/pm_pmo_analytics.duckdb`で、生成物はバージョン管理の対象外です。

| 入力ファイル | 内容 | 主な一意キー |
| --- | --- | --- |
| `projects.csv` | プロジェクト基本情報 | `project_id` |
| `resources.csv` | 役割ベースのリソース | `resource_id` |
| `resource_rates.csv` | 役割別時間単価と適用期間 | `resource_id`, `effective_start_date` |
| `wbs_progress.csv` | WBSのスナップショット進捗 | `project_id`, `wbs_id`, `snapshot_date` |
| `milestones.csv` | 節目の計画・実績 | `project_id`, `milestone_id` |
| `risks.csv` | リスク | `risk_id` |
| `issues.csv` | 課題 | `issue_id` |
| `change_requests.csv` | 変更要求 | `change_id` |
| `budget.csv` | 月次の予算・実績・見込 | `project_id`, `budget_month`, `budget_category` |
| `effort.csv` | リソース別の計画・実績工数 | `project_id`, `resource_id`, `work_date` |

## 処理フロー

1. `csv.DictReader`でCSVを読み込み、UTF-8のBOMを許容します。
2. 定義済みヘッダーとの完全一致を確認します。未定義列もエラーです。
3. 日付をISO形式の日付型、数値を`Decimal`、真偽値を真偽型へ変換します。
4. 必須値、列挙値、数値範囲、日付前後関係、複合キー重複、プロジェクト・リソース参照を検証します。単価期間の重複と、工数計上日に適用できる単価が1件だけであることも確認します。
5. すべての入力から日付を収集し、`dim_date`を生成します。
6. ディメンション、続いてファクトをロードします。日付列は`YYYYMMDD`の整数キーへ変換し、工数行には有効な単価と計画／実績人件費を付与します。
7. 完成した一時データベースを出力ファイルと置き換えます。

## エラー時の扱い

検証はDuckDB作成前に完了させます。検証エラー時はエラーとなったファイル、行、列、理由を表示し、出力データベースを変更しません。ロード中のエラーでも一時ファイルを削除し、正常に完成した場合だけ置換します。

## 更新運用

- プロジェクト基本情報は開始時と状態変更時に更新します。
- WBSはプロジェクト定例の基準日ごとにスナップショット行を追加します。同じWBS・同じ基準日の重複は許可しません。
- 予算と工数は月次締め後に更新します。
- 単価は役割単価の変更が決まった時点で有効開始日・終了日を更新します。過去期間の単価を上書きしません。
- リスク、課題、変更要求は発生・状態変更時に更新します。
- ダッシュボード表示前または定期処理でETLを再実行します。

## 実行コマンド

```sh
python -m bi.etl.run
python -m bi.etl.run --source-dir bi/data/source --database bi/data/pm_pmo_analytics.duckdb
```

入力CSVを変更せずに同じコマンドを再実行した場合、同じ論理データになります。
