"""
Admin Manage Issues Portal.
Full administrative management interface powered by v_issue_details view,
supporting manual assignment, auto-dispatch via MySQL stored procedure,
status updates (close/reject), and timeline inspection.
"""

import streamlit as st
from auth import require_role
from repositories.issue_repository import IssueRepository
from services.issue_service import IssueService
from services.assignment_service import AssignmentService
from services.user_service import UserService
from utils.ui_helpers import (
    inject_custom_css,
    render_sidebar,
    render_status_badge,
    render_priority_badge,
)

st.set_page_config(page_title="Manage Issues • Smart Campus", page_icon="⚙️", layout="wide")
inject_custom_css()
render_sidebar()

current_user = require_role(["admin"])

st.markdown("## ⚙️ Campus Issue Management")
st.caption("Review tickets, dispatch departmental technicians manually or via MySQL stored procedure, and close or reject complaints.")

# Load filter metadata
meta = IssueService.get_form_metadata()
categories = meta["categories"]
locations = meta["locations"]
priorities = meta["priorities"]
statuses = meta["statuses"]

# -------------------------------------------------------------
# FILTERS
# -------------------------------------------------------------
with st.container(border=True):
    st.markdown("##### 🔍 Search & Filters")
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)

    with f_col1:
        status_filter_opts = ["All Statuses"] + [s["status_name"] for s in statuses]
        sel_status = st.selectbox("Status", status_filter_opts)
        sel_status_id = next((s["status_id"] for s in statuses if s["status_name"] == sel_status), None) if sel_status != "All Statuses" else None

    with f_col2:
        cat_filter_opts = ["All Categories"] + [c["category_name"] for c in categories]
        sel_cat = st.selectbox("Category", cat_filter_opts)
        sel_cat_id = next((c["category_id"] for c in categories if c["category_name"] == sel_cat), None) if sel_cat != "All Categories" else None

    with f_col3:
        buildings = ["All Buildings"] + sorted(list(set(loc["building_name"] for loc in locations)))
        sel_bldg = st.selectbox("Building", buildings)

    with f_col4:
        prio_filter_opts = ["All Priorities"] + [p["level_name"] for p in priorities]
        sel_prio = st.selectbox("Priority", prio_filter_opts)
        sel_prio_id = next((p["priority_id"] for p in priorities if p["level_name"] == sel_prio), None) if sel_prio != "All Priorities" else None

    with f_col5:
        search_kw = st.text_input("Search Text", placeholder="Title, desc or student...")

# Fetch issues from view
issues = IssueRepository.get_all_issues(
    status_id=sel_status_id,
    category_id=sel_cat_id,
    building_name=sel_bldg if sel_bldg != "All Buildings" else None,
    priority_id=sel_prio_id,
    search_query=search_kw if search_kw.strip() else None,
)

st.markdown(f"**Total Records Found: {len(issues)}**")

if not issues:
    st.info("No issues matched your filter criteria.")
    st.stop()

# Render issue items
for issue in issues[:30]:  # Paginate top 30
    issue_id = issue["issue_id"]
    st_badge = render_status_badge(issue["status_name"])
    p_badge = render_priority_badge(issue["priority_level"])

    with st.container(border=True):
        c_hdr1, c_hdr2 = st.columns([3, 1])
        with c_hdr1:
            st.markdown(
                f"<h4 style='margin:0; padding:0;'>#{issue_id} — {issue['title']}</h4>",
                unsafe_allow_html=True,
            )
            st.caption(
                f"👤 Reported by: **{issue['reporter_name']}** ({issue['reporter_email']}) "
                f"| Category: **{issue['category_name']}** (Dept: **{issue['department_name']}**) "
                f"| 📍 {issue['building_name']} • Floor {issue['floor']} • Room {issue['room_number']} "
                f"| {issue['created_at'].strftime('%b %d, %Y %I:%M %p')}"
            )
        with c_hdr2:
            st.markdown(
                f"<div style='text-align: right;'>{st_badge} {p_badge}</div>",
                unsafe_allow_html=True,
            )
            if issue.get("assigned_technician_name"):
                st.caption(f"🔧 Assigned: **{issue['assigned_technician_name']}**")
            else:
                st.caption("⏳ *Unassigned*")

        # Action Drawer
        with st.expander(f"🛠️ Actions & Management Details for Issue #{issue_id}"):
            st.markdown(f"**Full Description:**\n{issue['description']}")

            tab_assign, tab_status, tab_hist = st.tabs([
                "⚡ Technician Assignment",
                "🔄 Update Status",
                "📜 Audit Timeline",
            ])

            # -------------------------------------------------------------
            # TAB 1: ASSIGN TECHNICIAN (Manual & Stored Procedure Auto-Assign)
            # -------------------------------------------------------------
            with tab_assign:
                if issue["status_name"] in ("resolved", "closed", "rejected"):
                    st.info(f"This issue is already **{issue['status_name']}** and cannot be assigned.")
                elif issue.get("assigned_technician_id"):
                    st.success(
                        f"Currently assigned to technician **{issue['assigned_technician_name']}** "
                        f"({issue['assigned_technician_email']}) since {issue['assigned_at'].strftime('%b %d, %I:%M %p')}."
                    )
                else:
                    st.markdown("##### Dispatch Technician")
                    a_col1, a_col2 = st.columns(2)

                    # Option A: Automatic Assignment via Stored Procedure
                    with a_col1:
                        with st.container(border=True):
                            st.markdown("###### 🤖 Auto-Assign (MySQL Stored Procedure)")
                            st.caption(
                                f"Executes `assign_least_loaded_technician` to identify the responsible "
                                f"department (**{issue['department_name']}**) and allocate the least-loaded technician."
                            )
                            if st.button("⚡ Run Auto-Assignment", key=f"auto_assign_{issue_id}", type="primary"):
                                with st.spinner("Invoking MySQL stored procedure with row locking..."):
                                    succ, msg, tech_id = AssignmentService.assign_auto(
                                        issue_id=issue_id, admin_id=current_user["user_id"]
                                    )
                                    if succ:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)

                    # Option B: Manual Assignment
                    with a_col2:
                        with st.container(border=True):
                            st.markdown("###### 👤 Manual Assignment")
                            dept_techs = UserService.get_technicians_for_department(issue["department_id"])

                            if not dept_techs:
                                st.warning(f"No active technicians found for {issue['department_name']}.")
                            else:
                                tech_labels = [f"{t['name']} ({t['email']})" for t in dept_techs]
                                tech_map = {f"{t['name']} ({t['email']})": t["user_id"] for t in dept_techs}

                                sel_tech_lbl = st.selectbox(
                                    "Select Technician",
                                    tech_labels,
                                    key=f"sel_tech_{issue_id}",
                                )
                                sel_tech_id = tech_map[sel_tech_lbl]
                                assign_notes = st.text_input("Dispatch Remarks", value="Manual admin assignment", key=f"notes_{issue_id}")

                                if st.button("📌 Confirm Manual Assignment", key=f"btn_man_{issue_id}"):
                                    with st.spinner("Executing assignment transaction..."):
                                        succ, msg = AssignmentService.assign_manual(
                                            issue_id=issue_id,
                                            technician_id=sel_tech_id,
                                            admin_id=current_user["user_id"],
                                            remarks=assign_notes,
                                        )
                                        if succ:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)

            # -------------------------------------------------------------
            # TAB 2: UPDATE STATUS (CLOSE / REJECT)
            # -------------------------------------------------------------
            with tab_status:
                st.markdown("##### Administrative Lifecycle Action")
                s_col1, s_col2 = st.columns(2)

                with s_col1:
                    with st.form(key=f"close_form_{issue_id}"):
                        st.markdown("###### ✅ Close Ticket")
                        st.caption("Mark issue officially verified and completed.")
                        close_remarks = st.text_input("Closing Remarks", value="Verified resolution on site.")
                        if st.form_submit_button("Close Ticket"):
                            succ, msg = IssueService.admin_update_status(
                                issue_id, "closed", current_user["user_id"], close_remarks
                            )
                            if succ:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                with s_col2:
                    with st.form(key=f"reject_form_{issue_id}"):
                        st.markdown("###### ❌ Reject Ticket")
                        st.caption("Reject duplicate, invalid, or unsubstantiated complaints.")
                        reject_remarks = st.text_input("Rejection Reason", placeholder="Explain rejection...")
                        if st.form_submit_button("Reject Ticket"):
                            if not reject_remarks.strip():
                                st.error("Please provide a reason for rejecting the complaint.")
                            else:
                                succ, msg = IssueService.admin_update_status(
                                    issue_id, "rejected", current_user["user_id"], reject_remarks
                                )
                                if succ:
                                    st.warning(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

            # -------------------------------------------------------------
            # TAB 3: AUDIT TIMELINE
            # -------------------------------------------------------------
            with tab_hist:
                hist_records = IssueService.get_issue_history(issue_id)
                if hist_records:
                    for h in hist_records:
                        st.markdown(
                            f"**{h['changed_at'].strftime('%d %b %Y, %I:%M %p')}** • "
                            f"{render_status_badge(h['new_status'])} by **{h['changed_by_name'] or 'System'}** "
                            f"({h['changed_by_role'] or 'Auto'}): *{h['remarks'] or 'No remarks'}*",
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No status history found.")
