# pm-pmo-ops-kit

PM・PMOが要件定義からプロジェクト終結までに使う文書、会議、管理台帳のテンプレート集です。プロジェクトの初期ドラフトを素早く用意し、承認・意思決定・進捗共有の抜け漏れを減らすことを目的にしています。

このリポジトリに含まれる内容はすべて架空のサンプルです。実在する会社名、顧客名、個人名、メールアドレス、IPアドレス、ドメイン、社内パス、ローカル環境固有の絶対パスは含めません。

## 内容

- `templates/`: 工程別の文書・会議・台帳テンプレート
- `docs/`: テンプレートの使い方と工程ゲートのガイド
- `scripts/`: テンプレート構成の検査と工程別チェックリスト出力
- `examples/`: 架空の案件データと記入例
- `.github/`: GitHub Actions、Issue、PR テンプレート

## テンプレート一覧

| 工程 | 主なテンプレート |
| --- | --- |
| 構想・立上げ | プロジェクト憲章、ステークホルダー一覧、キックオフアジェンダ |
| 要件定義 | 要件定義書、要件トレーサビリティ、意思決定ログ |
| 計画 | WBS、体制・RACI、リスク・課題・変更管理台帳、コミュニケーション計画 |
| 設計・開発 | 設計レビュー、進捗報告、課題エスカレーション |
| テスト・移行 | テスト計画、受入判定、移行・リリース計画 |
| 終結 | プロジェクト完了報告、振り返り |

あわせて、予算・リソースの基準線と実績、完了後の便益・成果指標を管理するテンプレートを含みます。

## BI分析・可視化

架空のプロジェクト基本情報、WBS・進捗、マイルストーン、リスク・課題、変更要求、予算・実績、リソース・工数、役割別時間単価を対象に、品質検証からDuckDBへの格納、分析SQL、Streamlitダッシュボードまでをローカルで再現できます。既存テンプレートや既存スクリプトを置き換えるものではなく、`bi/`配下に独立して追加しています。

```sh
python -m pip install -e ".[bi,dev]"
python -m bi.etl.run
python -m streamlit run bi/app/dashboard.py
```

ダッシュボードはエグゼクティブサマリー、進捗分析、予算・工数分析、リスク・課題分析の4画面で構成され、プロジェクト・期間の絞り込み、役割別単価を適用した人件費の確認、KPI定義の確認、表のCSV出力に対応します。

- [BIアーキテクチャ](docs/bi-architecture.md)
- [データモデル定義](docs/bi-data-model.md)
- [KPI定義書](docs/bi-kpi-definition.md)
- [ETL設計書](docs/bi-etl-design.md)
- [データ品質ルール](docs/bi-data-quality-rules.md)
- [ダッシュボード操作ガイド](docs/bi-dashboard-guide.md)
- [ローカル環境構築手順](docs/bi-local-setup.md)
- [BIエンジニアとしての設計判断](docs/bi-design-decisions.md)

## フロー図・工程イメージ

- [プロジェクトフローとガントチャート](docs/project-flow.md): 工程ゲート、継続的な管理活動、標準的な進行イメージ
- [プロジェクトライフサイクルの使い方](docs/project-lifecycle.md): 各工程の目的、完了条件、利用するテンプレート
- [進捗KPIの使い方](docs/project-kpis.md): 進捗率、マイルストーン、期限超過、計画対実績の判断方法

## 使い方

1. `docs/project-lifecycle.md` で対象工程と完了条件を確認します。
2. `templates/` から必要な文書をコピーし、案件の規程・契約・承認経路に合わせて編集します。
3. `examples/sample-project-register.csv` を参照して、管理台帳の粒度を調整します。
4. 定例ごとに課題、リスク、変更、意思決定を更新し、関係者へ共有します。

工程別の確認項目を出力できます。

```sh
python scripts/generate_project_checklist.py requirements
python scripts/generate_project_checklist.py delivery
python scripts/generate_project_checklist.py closure
```

テンプレートの必須見出しを検査します。

```sh
python scripts/validate_templates.py templates
```

テストを実行します。

```sh
python -m pytest
ruff check .
ruff format --check .
```

## 運用上の注意

- テンプレートは組織の規程、契約、セキュリティ要件を置き換えるものではありません。
- 個人情報、認証情報、未公開の事業情報を記載・コミットしないでください。
- 承認者、決裁条件、変更管理のルールは案件開始時に明確化してください。
- 文書の版、決定日、決定者、根拠を残し、最新版の所在を一本化してください。

## ライセンス

必要に応じてライセンスファイルを追加してください。
