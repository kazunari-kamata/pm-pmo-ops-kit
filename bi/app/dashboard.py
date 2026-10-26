"""PM・PMO運営データを確認する日本語Streamlitダッシュボード。"""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from bi.app.queries import (
    DEFAULT_DATABASE_PATH,
    project_options,
    query_records,
    reporting_date_range,
)
from bi.models.kpi import KPI_DEFINITIONS

st.set_page_config(page_title="PM・PMO 分析ダッシュボード", page_icon="📊", layout="wide")


def _number(value: Any, suffix: str = "") -> str:
    if value is None:
        return "—"
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float):
        return f"{value:,.1f}{suffix}"
    return f"{value:,}{suffix}"


def _records_to_csv(records: list[dict[str, Any]]) -> bytes:
    if not records:
        return b""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue().encode("utf-8-sig")


def _download(records: list[dict[str, Any]], filename: str) -> None:
    st.download_button(
        "CSVを出力",
        data=_records_to_csv(records),
        file_name=filename,
        mime="text/csv",
        disabled=not records,
    )


def _show_table(records: list[dict[str, Any]], filename: str) -> None:
    if not records:
        st.info("選択条件に該当するデータはありません。")
        return
    st.dataframe(records, use_container_width=True, hide_index=True)
    _download(records, filename)


def _show_kpi_definitions() -> None:
    with st.expander("KPIの定義・判定基準を確認"):
        for definition in KPI_DEFINITIONS:
            st.markdown(f"**{definition.name}** — {definition.purpose}")
            st.caption(
                f"計算式: {definition.formula}　/　"
                f"NULL・ゼロ: {definition.zero_and_null}　/　"
                f"判断: {definition.judgement}"
            )


def _bar_chart(
    records: list[dict[str, Any]],
    x_key: str,
    series: list[tuple[str, str]],
    title: str,
    barmode: str = "group",
) -> None:
    if not records:
        st.info("グラフに表示するデータはありません。")
        return
    figure = go.Figure()
    for value_key, label in series:
        figure.add_bar(
            x=[str(record[x_key]) for record in records],
            y=[record.get(value_key) for record in records],
            name=label,
        )
    figure.update_layout(title=title, barmode=barmode, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(figure, use_container_width=True)


def _attention_projects(kpis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in kpis
        if row["overdue_task_count"] > 0
        or row["high_risk_count"] > 0
        or row["budget_overrun_amount"] > 0
        or row["unresolved_issue_count"] > 0
    ]


def executive_summary(kpis: list[dict[str, Any]]) -> None:
    st.header("エグゼクティブサマリー")
    if not kpis:
        st.info("選択条件に該当するプロジェクトはありません。")
        return
    total_planned_budget = sum((row["planned_budget_amount"] or 0) for row in kpis)
    total_actual_budget = sum((row["actual_budget_amount"] or 0) for row in kpis)
    high_risk_projects = sum(1 for row in kpis if row["high_risk_count"] > 0)
    overdue_tasks = sum(row["overdue_task_count"] for row in kpis)
    budget_rate = 100 * total_actual_budget / total_planned_budget if total_planned_budget else None
    columns = st.columns(4)
    columns[0].metric("対象プロジェクト", f"{len(kpis)}件")
    columns[1].metric("予算消化率", _number(budget_rate, "%"))
    columns[2].metric("高リスク案件数", f"{high_risk_projects}件")
    columns[3].metric("期限超過タスク", f"{overdue_tasks}件")
    _bar_chart(
        kpis,
        "project_name",
        [("progress_rate_pct", "進捗率 (%)"), ("milestone_achievement_rate_pct", "節目達成率 (%)")],
        "プロジェクト別の進捗・マイルストーン達成率",
    )
    st.subheader("プロジェクト別KPI")
    _show_table(kpis, "project_kpis.csv")
    st.subheader("注意が必要なプロジェクト")
    attention = _attention_projects(kpis)
    if attention:
        _show_table(attention, "attention_projects.csv")
    else:
        st.success("設定した注意条件（期限超過・高リスク・予算超過・未解決課題）に該当しません。")


def progress_analysis(
    kpis: list[dict[str, Any]], database_path: Path, filters: dict[str, Any]
) -> None:
    st.header("進捗分析")
    _bar_chart(
        kpis,
        "project_name",
        [("progress_rate_pct", "進捗率 (%)"), ("schedule_variance_days", "日程差異 (日)")],
        "プロジェクト別進捗と日程差異",
    )
    tasks = query_records(database_path, "task_details", **filters)
    milestones = query_records(database_path, "milestone_details", **filters)
    _bar_chart(
        tasks,
        "task_name",
        [("planned_progress_pct", "計画進捗 (%)"), ("actual_progress_pct", "実績進捗 (%)")],
        "WBS作業の計画対実績進捗",
    )
    st.subheader("期限超過タスク")
    overdue = [record for record in tasks if record["is_overdue"]]
    _show_table(overdue, "overdue_tasks.csv")
    st.subheader("マイルストーン達成状況")
    _show_table(milestones, "milestones.csv")


def budget_effort_analysis(
    kpis: list[dict[str, Any]], database_path: Path, filters: dict[str, Any]
) -> None:
    st.header("予算・工数分析")
    _bar_chart(
        kpis,
        "project_name",
        [
            ("planned_budget_amount", "計画予算"),
            ("actual_budget_amount", "実績予算"),
            ("forecast_budget_amount", "見込予算"),
        ],
        "プロジェクト別予算",
    )
    _bar_chart(
        kpis,
        "project_name",
        [("planned_labor_cost", "計画人件費"), ("actual_labor_cost", "実績人件費")],
        "プロジェクト別人件費（工数 × 適用時間単価）",
    )
    monthly = query_records(database_path, "monthly_budget_effort", **filters)
    st.subheader("月次の予算・工数")
    _bar_chart(
        monthly,
        "month_date",
        [("planned_budget_amount", "計画予算"), ("actual_budget_amount", "実績予算")],
        "月次予算推移",
    )
    _show_table(monthly, "monthly_budget_effort.csv")
    st.subheader("プロジェクト別・役割別工数・適用単価・人件費")
    resources = query_records(database_path, "resource_effort", **filters)
    _show_table(resources, "resource_effort.csv")


def risk_issue_analysis(database_path: Path, filters: dict[str, Any]) -> None:
    st.header("リスク・課題分析")
    records = query_records(database_path, "risk_issue_breakdown", **filters)
    if records:
        severity_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        today = filters["end_date"]
        for record in records:
            severity_counts[record["severity"]] = severity_counts.get(record["severity"], 0) + 1
            status = record["record_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            record["未解決日数"] = (
                (today - record["registered_date"]).days
                if record["resolved_date"] is None
                else None
            )
        count_rows = [
            {"区分": "重要度", "値": key, "件数": value} for key, value in severity_counts.items()
        ] + [{"区分": "状態", "値": key, "件数": value} for key, value in status_counts.items()]
        _bar_chart(count_rows, "値", [("件数", "件数")], "重要度・ステータス別件数")
    st.subheader("リスク・課題一覧と未解決期間")
    _show_table(records, "risk_issue_records.csv")


def main() -> None:
    st.title("PM・PMO 運営分析ダッシュボード")
    st.caption("架空CSVをETLでDuckDBへ格納したローカル分析サンプルです。")
    database_path = DEFAULT_DATABASE_PATH
    if not database_path.is_file():
        st.error("分析データベースがありません。READMEのETL実行手順に従って生成してください。")
        return
    date_range = reporting_date_range(database_path)
    if date_range is None:
        st.info("表示できるスナップショットデータがありません。")
        return
    projects = project_options(database_path)
    labels = {"すべて": None} | {
        f"{project['project_name']} ({project['project_id']})": project["project_id"]
        for project in projects
    }
    with st.sidebar:
        st.header("絞り込み")
        project_label = st.selectbox("プロジェクト", list(labels))
        selected_period = st.date_input(
            "対象期間", value=date_range, min_value=date_range[0], max_value=date_range[1]
        )
        page = st.radio(
            "画面",
            ["エグゼクティブサマリー", "進捗分析", "予算・工数分析", "リスク・課題分析"],
        )
    if not isinstance(selected_period, tuple) or len(selected_period) != 2:
        st.warning("開始日と終了日を選択してください。")
        return
    start_date, end_date = selected_period
    if start_date > end_date:
        st.warning("開始日は終了日以前にしてください。")
        return
    filters = {"project_id": labels[project_label], "start_date": start_date, "end_date": end_date}
    kpis = query_records(database_path, "kpi_by_project", **filters)
    _show_kpi_definitions()
    if page == "エグゼクティブサマリー":
        executive_summary(kpis)
    elif page == "進捗分析":
        progress_analysis(kpis, database_path, filters)
    elif page == "予算・工数分析":
        budget_effort_analysis(kpis, database_path, filters)
    else:
        risk_issue_analysis(database_path, filters)


if __name__ == "__main__":
    main()
