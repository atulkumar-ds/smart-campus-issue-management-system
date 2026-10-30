"""
Technician "My Tasks" Portal.
Displays assigned maintenance work orders, status actions (In Progress, Resolved),
resolution remarks recording, and live technician workload gauge.
"""

import streamlit as st
from auth import require_role
from services.assignment_service import AssignmentService
from services.issue_service import IssueService
from utils.ui_helpers import (
    inject_custom_css,
    render_sidebar,
    render_status_badge,
    render_priority_badge,
)

st.set_page_config(page_title="My Work Orders • Smart Campus", page_icon="🔧", layout="wide")
inject_custom_css()
render_sidebar()

current_user = require_role(["technician"])

st.markdown(f"## 🔧 Technician Work Orders — {current_user['name']}")
st.caption(f"Assigned department: **{current_user.get('department_name', 'Operations')}** • ID #{current_user['user_id']}")

# Fetch tasks
tasks = AssignmentService.get_technician_tasks(current_user["user_id"])
active_tasks = [t for t in tasks if t["status_name"] not in ("resolved", "closed", "rejected")]

# Workload Summary Metric
w_col1, w_col2, w_col3 = st.columns(3)
with w_col1:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #2563EB;">
            <div class="metric-title">Active Workload</div>
            <div class="metric-value" style="color: #2563EB;">{len(active_tasks)} Tasks</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with w_col2:
    resolved_count = sum(1 for t in tasks if t["status_name"] in ("resolved", "closed"))
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #059669;">
            <div class="metric-title">Resolved by You</div>
            <div class="metric-value" style="color: #059669;">{resolved_count} Tasks</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with w_col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Total Lifetime Dispatches</div>
            <div class="metric-value">{len(tasks)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Filter Tabs: Active vs Completed
tab_active, tab_history = st.tabs([f"⚡ Active Tasks ({len(active_tasks)})", f"✅ Completed / Closed ({resolved_count})"])

with tab_active:
    if not active_tasks:
        st.success("🎉 You have no pending active tasks assigned right now!")
    else:
        for t in active_tasks:
            issue_id = t["issue_id"]
            st_badge = render_status_badge(t["status_name"])
            p_badge = render_priority_badge(t["priority_level"])

            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"#### #{issue_id} — {t['title']}")
                    st.caption(
                        f"📍 **{t['building_name']} • Floor {t['floor']} • Room {t['room_number']}** "
                        f"| Category: **{t['category_name']}** "
                        f"| Reported by: **{t['reporter_name']}**"
                    )
                    st.markdown(f"**Issue Description:**\n{t['description']}")
                    st.caption(
                        f"Assigned At: {t['assigned_at'].strftime('%b %d, %I:%M %p')} "
                        f"| Expected SLA Completion: **{t['expected_completion'].strftime('%b %d, %I:%M %p') if t.get('expected_completion') else 'N/A'}**"
                    )
                with c2:
                    st.markdown(f"<div style='text-align:right;'>{st_badge} {p_badge}</div>", unsafe_allow_html=True)

                st.divider()

                # Action Buttons
                act_c1, act_c2 = st.columns(2)

                # Action 1: Mark In Progress
                with act_c1:
                    if t["status_name"] == "assigned":
                        if st.button("🚀 Start Work (Mark In Progress)", key=f"prog_{issue_id}", type="secondary", use_container_width=True):
                            succ, msg = AssignmentService.set_in_progress(issue_id, current_user["user_id"])
                            if succ:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.info("Status is currently **In Progress**.")

                # Action 2: Mark Resolved
                with act_c2:
                    with st.expander("✅ Mark as Resolved & Enter Remarks"):
                        with st.form(key=f"res_form_{issue_id}"):
                            remarks = st.text_area(
                                "Resolution Remarks *",
                                placeholder="Explain what repair or replacement was conducted...",
                                help="Detail the solution (at least 5 characters).",
                            )
                            submit_res = st.form_submit_button("Complete & Mark Resolved", type="primary", use_container_width=True)
                            if submit_res:
                                if not remarks or len(remarks.strip()) < 5:
                                    st.error("Please enter descriptive resolution remarks (minimum 5 characters).")
                                else:
                                    succ, msg = AssignmentService.resolve_task(issue_id, current_user["user_id"], remarks)
                                    if succ:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)

with tab_history:
    completed_tasks = [t for t in tasks if t["status_name"] in ("resolved", "closed", "rejected")]
    if not completed_tasks:
        st.info("No completed tasks to display.")
    else:
        for ct in completed_tasks[:20]:
            with st.container(border=True):
                st.markdown(
                    f"**#{ct['issue_id']} — {ct['title']}** &nbsp; {render_status_badge(ct['status_name'])}",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"📍 {ct['building_name']} • Room {ct['room_number']} "
                    f"| Category: {ct['category_name']} "
                    f"| Completed At: {ct['completed_at'].strftime('%b %d, %Y %I:%M %p') if ct.get('completed_at') else 'N/A'}"
                )
