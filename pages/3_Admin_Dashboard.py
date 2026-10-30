"""
Administrative Analytics Dashboard.
Displays live KPI metric cards, SLA breach alerts, and interactive Plotly charts
queried directly from MySQL 8.0 views and tables.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from auth import require_role
from services.analytics_service import AnalyticsService
from repositories.issue_repository import IssueRepository
from utils.ui_helpers import (
    inject_custom_css,
    render_sidebar,
    render_status_badge,
    render_priority_badge,
)

st.set_page_config(page_title="Operations Dashboard • Smart Campus", page_icon="📊", layout="wide")
inject_custom_css()
render_sidebar()

# Role Protection: Administrator only
current_user = require_role(["admin"])

st.markdown("## 📊 Campus Facilities Operations Dashboard")
st.caption("Live relational database telemetry, SLA breach monitoring, and workload intelligence.")

# -------------------------------------------------------------
# 1. TOP-LEVEL SUMMARY METRIC CARDS
# -------------------------------------------------------------
metrics = AnalyticsService.get_summary_metrics()

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Total Issues Logged</div>
            <div class="metric-value">{metrics.get('total_issues', 0)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi2:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #2563EB;">
            <div class="metric-title">Open & Unassigned</div>
            <div class="metric-value" style="color: #2563EB;">{metrics.get('open_issues', 0)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi3:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #D97706;">
            <div class="metric-title">In Progress</div>
            <div class="metric-value" style="color: #D97706;">{metrics.get('in_progress_issues', 0)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi4:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #059669;">
            <div class="metric-title">Resolved / Closed</div>
            <div class="metric-value" style="color: #059669;">{metrics.get('resolved_issues', 0) + metrics.get('closed_issues', 0)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with kpi5:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #DC2626;">
            <div class="metric-title">SLA Breaches / Overdue</div>
            <div class="metric-value" style="color: #DC2626;">{metrics.get('overdue_issues', 0)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. INTERACTIVE PLOTLY CHARTS (ROW 1)
# -------------------------------------------------------------
ch_col1, ch_col2 = st.columns(2)

with ch_col1:
    with st.container(border=True):
        st.markdown("#### 📁 Issues by Category")
        df_cat = AnalyticsService.get_issues_by_category()
        if not df_cat.empty:
            fig_cat = px.bar(
                df_cat,
                x="category_name",
                y="issue_count",
                color="category_name",
                labels={"category_name": "Category", "issue_count": "Total Complaints"},
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            fig_cat.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20), height=320)
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.caption("No data available.")

with ch_col2:
    with st.container(border=True):
        st.markdown("#### 🏢 Issues by Campus Building")
        df_bldg = AnalyticsService.get_issues_by_building()
        if not df_bldg.empty:
            fig_bldg = px.bar(
                df_bldg,
                x="issue_count",
                y="building_name",
                orientation="h",
                labels={"building_name": "Building", "issue_count": "Total Issues"},
                color="issue_count",
                color_continuous_scale="Blues",
            )
            fig_bldg.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=20, b=20), height=320)
            st.plotly_chart(fig_bldg, use_container_width=True)
        else:
            st.caption("No data available.")

# -------------------------------------------------------------
# 3. INTERACTIVE PLOTLY CHARTS (ROW 2)
# -------------------------------------------------------------
ch_col3, ch_col4 = st.columns(2)

with ch_col3:
    with st.container(border=True):
        st.markdown("#### 📈 Reported vs. Resolved Monthly Trend")
        df_trend = AnalyticsService.get_reported_vs_resolved_trend()
        if not df_trend.empty:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=df_trend["month_year"],
                y=df_trend["reported"],
                name="Reported",
                marker_color="#2563EB",
            ))
            fig_trend.add_trace(go.Bar(
                x=df_trend["month_year"],
                y=df_trend["resolved"],
                name="Resolved",
                marker_color="#059669",
            ))
            fig_trend.update_layout(
                barmode="group",
                margin=dict(l=20, r=20, t=20, b=20),
                height=320,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.caption("No data available.")

with ch_col4:
    with st.container(border=True):
        st.markdown("#### ⏱️ Average Resolution Time by Department (Hours)")
        df_res_dept = AnalyticsService.get_avg_resolution_by_department()
        if not df_res_dept.empty:
            fig_dept_res = px.bar(
                df_res_dept,
                x="department_name",
                y="avg_hours",
                labels={"department_name": "Department", "avg_hours": "Avg Resolution Hours"},
                color="avg_hours",
                color_continuous_scale="Tealgrn",
            )
            fig_dept_res.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
            st.plotly_chart(fig_dept_res, use_container_width=True)
        else:
            st.caption("No data available.")

# -------------------------------------------------------------
# 4. INTERACTIVE PLOTLY CHARTS (ROW 3)
# -------------------------------------------------------------
ch_col5, ch_col6 = st.columns(2)

with ch_col5:
    with st.container(border=True):
        st.markdown("#### 🔧 Active Technician Workload (v_technician_workload)")
        df_workload = AnalyticsService.get_technician_workload()
        if not df_workload.empty:
            fig_wl = px.bar(
                df_workload,
                x="technician_name",
                y="active_task_count",
                color="department_name",
                labels={"technician_name": "Technician", "active_task_count": "Active Uncompleted Tasks"},
            )
            fig_wl.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig_wl, use_container_width=True)
        else:
            st.caption("No data available.")

with ch_col6:
    with st.container(border=True):
        st.markdown("#### 🚨 Issue Priority Distribution")
        df_prio = AnalyticsService.get_priority_distribution()
        if not df_prio.empty:
            fig_prio = px.pie(
                df_prio,
                names="priority",
                values="issue_count",
                hole=0.45,
                color="priority",
                color_discrete_map={
                    "Low": "#2563EB",
                    "Medium": "#0D9488",
                    "High": "#D97706",
                    "Critical": "#DC2626",
                },
            )
            fig_prio.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig_prio, use_container_width=True)
        else:
            st.caption("No data available.")

# -------------------------------------------------------------
# 5. DEPARTMENT BACKLOG & OVERDUE ISSUES TABLES
# -------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
t_col1, t_col2 = st.columns(2)

with t_col1:
    with st.container(border=True):
        st.markdown("#### 🏛️ Department Unresolved Workload (v_open_issues_by_department)")
        df_dept_wl = AnalyticsService.get_department_backlog_view()
        if not df_dept_wl.empty:
            st.dataframe(
                df_dept_wl[[
                    "department_name",
                    "open_issues",
                    "in_progress_issues",
                    "total_unresolved_issues",
                ]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No data available.")

with t_col2:
    with st.container(border=True):
        st.markdown("#### ⚠️ Active SLA Breaches (v_overdue_issues)")
        overdue_list = AnalyticsService.get_overdue_issues_list()
        if overdue_list:
            for ov in overdue_list[:5]:
                st.markdown(
                    f"**#{ov['issue_id']} • {ov['title']}** "
                    f"({render_priority_badge(ov['priority_level'])}) "
                    f"— <span style='color:#DC2626; font-weight:bold;'>{ov['hours_overdue']} hrs overdue</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"📍 {ov['building_name']} • {ov['room_number']} | Dept: {ov['department_name']}")
                st.markdown("<hr style='margin:0.25rem 0;'>", unsafe_allow_html=True)
        else:
            st.success("🎉 No issues are currently breaching SLA limits!")
