"""ダッシュボードと定義書で共有するKPIのメタデータ。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KpiDefinition:
    key: str
    name: str
    purpose: str
    formula: str
    zero_and_null: str
    judgement: str


KPI_DEFINITIONS = (
    KpiDefinition(
        "progress_rate_pct",
        "プロジェクト進捗率",
        "WBSで定義した作業の完了状況を把握する。",
        "基準日時点で完了のWBS作業数 ÷ 対象WBS作業数 × 100",
        "対象作業が0件の場合はNULL（画面では「—」）とする。",
        "計画との差異、期限超過、ブロック有無を併せて確認する。",
    ),
    KpiDefinition(
        "schedule_variance_days",
        "計画対実績差異",
        "日程の回復要否を判断する。",
        "作業ごとの実績完了日（未完了かつ期限超過は基準日）－予定完了日の平均日数",
        "対象作業が0件の場合はNULLとする。未来の予定作業は差異0日とする。",
        "正の値は遅延、0以下は予定どおり又は前倒しとして扱う。",
    ),
    KpiDefinition(
        "milestone_achievement_rate_pct",
        "マイルストーン達成率",
        "重要な合意・成果物の遅延を把握する。",
        "基準日までに期限内完了した節目数 ÷ 基準日までが期限の節目数 × 100",
        "期限到来済み節目が0件の場合はNULLとする。",
        "期限超過又は未完了の節目は要確認とする。",
    ),
    KpiDefinition(
        "overdue_task_count",
        "期限超過タスク数",
        "対応が必要な滞留作業を特定する。",
        "基準日前に予定完了日があり、未完了のWBS作業数",
        "該当なしは0件とする。",
        "1件以上は担当・依存関係・回復策を確認する。",
    ),
    KpiDefinition(
        "unresolved_issue_count",
        "未解決課題数",
        "解決されていない阻害要因を把握する。",
        "基準日までに登録され、状態がオープン又は対応中の課題数",
        "該当なしは0件とする。",
        "高重要度又は期限超過の課題を優先して確認する。",
    ),
    KpiDefinition(
        "average_issue_resolution_days",
        "課題平均解決日数",
        "課題解決のリードタイムを把握する。",
        "解決済み課題の解決日－登録日の平均日数",
        "解決済み課題が0件の場合はNULLとする。",
        "長期化の傾向は原因と対処を確認する。",
    ),
    KpiDefinition(
        "high_risk_count",
        "高リスク案件数",
        "エスカレーションが必要なリスクのある案件を特定する。",
        "未解決かつ重要度「高」のリスクを持つプロジェクト数",
        "全体集計ではプロジェクト単位で重複なく数える。",
        "1件以上のプロジェクトは注意対象とする。",
    ),
    KpiDefinition(
        "budget_consumption_rate_pct",
        "予算消化率",
        "計画予算に対する実績支出の進行度を把握する。",
        "対象期間の実績額 ÷ 対象期間の計画額 × 100",
        "計画額が0の場合はNULLとする。",
        "100%超は予算超過額を併せて確認する。",
    ),
    KpiDefinition(
        "budget_overrun_amount",
        "予算超過額",
        "予算枠を上回る実績を把握する。",
        "max(対象期間の実績額－対象期間の計画額, 0)",
        "対象実績がない場合は0とする。",
        "正の値は承認済み変更と対処を確認する。",
    ),
    KpiDefinition(
        "effort_actual_vs_plan_rate_pct",
        "計画工数対実績工数",
        "工数見積りと実績の乖離を把握する。",
        "対象期間の実績工数 ÷ 対象期間の計画工数 × 100",
        "計画工数が0の場合はNULLとする。",
        "100%超は超過傾向として確認する。",
    ),
    KpiDefinition(
        "labor_cost_actual_vs_plan_rate_pct",
        "計画人件費対実績人件費",
        "工数と適用単価を反映した人件費の乖離を把握する。",
        "対象期間の実績人件費 ÷ 対象期間の計画人件費 × 100",
        "計画人件費が0の場合はNULLとする。",
        "100%超は工数差異と単価差異を確認する。",
    ),
)
