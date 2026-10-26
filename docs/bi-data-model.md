# BIデータモデル定義

## 設計方針

分析モデルはスタースキーマです。プロジェクト・日付・リソースを共通ディメンションとし、事実が発生する業務粒度でファクトを分離します。複数のファクトを明細のまま結合せず、分析SQL内で各ファクトを先にプロジェクト単位へ集計してから結合するため、課題数と予算行数の掛け合わせによる二重計上を防ぎます。

## ディメンション

| テーブル | 主キー | 粒度 | 主な列（型、NULL可否） | 出所・更新 |
| --- | --- | --- | --- | --- |
| `dim_project` | `project_key` | 1プロジェクト1行 | `project_name` VARCHAR NOT NULL、`portfolio` VARCHAR NOT NULL、計画・実績開始終了日 DATE（一部NULL可） | `projects.csv`。基本情報・状態変更時に全置換 |
| `dim_date` | `date_key` | 暦日1日1行 | `calendar_date` DATE NOT NULL、`year_number` INTEGER NOT NULL、`month_number` INTEGER NOT NULL、`year_month` VARCHAR NOT NULL | 全入力の日付からETLで生成 |
| `dim_resource` | `resource_key` | 役割ベースのリソース1件1行 | `resource_name` VARCHAR NOT NULL、`role` VARCHAR NOT NULL | `resources.csv`。体制変更時に全置換 |
| `dim_resource_rate` | `resource_rate_key`。FK: リソース、有効開始・終了日 | リソース・単価適用期間1件 | 計画・実績時間単価 DECIMAL NOT NULL、通貨 VARCHAR NOT NULL、終了日キーはNULL可 | `resource_rates.csv`。単価改定時に期間行を追加 |

`project_key`と`resource_key`はCSVのIDをそのまま使用します。日付キーは`YYYYMMDD`の整数です。

## ファクト

| テーブル | 主キー・外部キー | 粒度 | 主な列（型、NULL可否） | 出所・更新 |
| --- | --- | --- | --- | --- |
| `fact_progress` | PK: プロジェクト・WBS・スナップショット日。FK: プロジェクト、各日付 | WBS作業の基準日スナップショット1件 | 状態 VARCHAR NOT NULL、計画・実績進捗 DECIMAL NOT NULL、計画・実績工数 DECIMAL NOT NULL、ブロック BOOLEAN NOT NULL、実績日付キーはNULL可 | `wbs_progress.csv`。定例ごとに追記 |
| `fact_milestone` | PK: プロジェクト・節目ID。FK: プロジェクト、計画・実績日付 | 節目1件 | 節目名 VARCHAR NOT NULL、状態 VARCHAR NOT NULL、実績日付キーはNULL可 | `milestones.csv`。節目更新時に更新 |
| `fact_issue` | PK: 課題ID。FK: プロジェクト、登録・期限・解決日付 | 課題1件 | 件名 VARCHAR NOT NULL、重要度 VARCHAR NOT NULL、状態 VARCHAR NOT NULL、期限・解決日はNULL可 | `issues.csv`。発生・解決時に更新 |
| `fact_risk` | PK: リスクID。FK: プロジェクト、登録・期限・解決日付 | リスク1件 | 件名、重要度、発生確率、影響、状態はいずれもVARCHAR NOT NULL。期限・解決日はNULL可 | `risks.csv`。発生・対応時に更新 |
| `fact_change_request` | PK: 変更ID。FK: プロジェクト、申請・決定日付 | 変更要求1件 | 件名 VARCHAR NOT NULL、状態 VARCHAR NOT NULL、費用影響 DECIMAL NOT NULL、日程影響 INTEGER NOT NULL、決定日はNULL可 | `change_requests.csv`。申請・決定時に更新 |
| `fact_budget` | PK: プロジェクト・予算月・費目。FK: プロジェクト、予算月 | 月次・費目別の予算1件 | 計画・実績・見込金額 DECIMAL NOT NULL | `budget.csv`。月次締め後に更新 |
| `fact_effort` | PK: プロジェクト・リソース・作業日。FK: プロジェクト、リソース、適用単価、作業日 | 日次又は月次集計した役割別工数1件 | 計画・実績工数、適用済み計画・実績時間単価、計画・実績人件費はいずれもDECIMAL NOT NULL | `effort.csv`と`resource_rates.csv`。定例又は月次で更新 |

## 結合と集計上の注意

- `fact_progress`は履歴を保持します。進捗KPIでは基準日以前の各プロジェクト・WBSの最新行だけを採用します。
- `fact_budget`と`fact_effort`は月別のため、期間指定時は開始日から終了日までを合算します。
- `fact_effort`の人件費は、作業日に有効な`dim_resource_rate`をETLで参照して確定します。単価履歴を明細結合せず、適用済み単価と計算済み人件費をファクトへ保持します。
- 課題・リスクの状態指標は、基準日までに登録されたレコードを対象にします。
- プロジェクト横断の高リスク案件数は、リスク行数ではなく、高リスクを1件以上持つプロジェクト数を数えます。
