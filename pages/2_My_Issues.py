"""
Student / Staff "My Issues" Tracking Portal.
Displays reporter's tickets, audit timeline from issue_status_history,
comment thread, and post-resolution feedback submission.
"""

import streamlit as st
from auth import require_role
from services.issue_service import IssueService
from utils.ui_helpers import (
    inject_custom_css,
    render_sidebar,
    render_status_badge,
    render_priority_badge,
)

st.set_page_config(page_title="My Reported Issues • Smart Campus", page_icon="📋", layout="wide")
inject_custom_css()
render_sidebar()

current_user = require_role(["student", "staff"])

st.markdown("## 📋 My Reported Issues")
st.caption(f"Track the status and timeline of complaints filed by **{current_user['name']}**.")

# Fetch user's issues
issues = IssueService.get_student_issues(current_user["user_id"])

if not issues:
    st.info("You haven't reported any campus issues yet. Click below to file a new report.")
    st.page_link("pages/1_Report_Issue.py", label="Report an Issue", icon="✍️")
    st.stop()

# Filters
c1, c2 = st.columns([1, 2])
with c1:
    statuses = ["All Statuses"] + sorted(list(set(i["status_name"] for i in issues)))
    selected_status = st.selectbox("Filter by Status", statuses)
with c2:
    search_term = st.text_input("Search my issues", placeholder="Search by title, location or category...")

filtered = issues
if selected_status != "All Statuses":
    filtered = [i for i in filtered if i["status_name"] == selected_status]
if search_term:
    st_lower = search_term.lower()
    filtered = [
        i for i in filtered
        if st_lower in i["title"].lower()
        or st_lower in i["category_name"].lower()
        or st_lower in i["building_name"].lower()
        or st_lower in str(i["issue_id"])
    ]

st.markdown(f"**Showing {len(filtered)} tickets**")

for issue in filtered:
    issue_id = issue["issue_id"]
    status_badge = render_status_badge(issue["status_name"])
    priority_badge = render_priority_badge(issue["priority_level"])

    with st.container(border=True):
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.markdown(
                f"<h4 style='margin:0; padding:0;'>#{issue_id} — {issue['title']}</h4>",
                unsafe_allow_html=True,
            )
            st.caption(
                f"📍 {issue['building_name']} • Floor {issue['floor']} • Room {issue['room_number']} "
                f"| Category: **{issue['category_name']}** ({issue['department_name']}) "
                f"| Reported: {issue['created_at'].strftime('%b %d, %Y %I:%M %p')}"
            )
        with col_hdr2:
            st.markdown(
                f"<div style='text-align: right;'>{status_badge} {priority_badge}</div>",
                unsafe_allow_html=True,
            )
            if issue.get("assigned_technician_name"):
                st.caption(f"🔧 Tech: **{issue['assigned_technician_name']}**")
            else:
                st.caption("⏳ Awaiting technician assignment")

        # Expander for full details, history, comments, and feedback
        with st.expander(f"🔍 View Full Details & Progress Timeline for #{issue_id}"):
            st.markdown(f"**Description:**\n{issue['description']}")
            if issue.get("resolved_at"):
                st.success(f"✅ Resolved on: {issue['resolved_at'].strftime('%b %d, %Y %I:%M %p')}")

            tab_timeline, tab_comments, tab_feedback = st.tabs([
                "⏱️ Status History & Timeline",
                "💬 Comments",
                "⭐ Feedback",
            ])

            # -------------------------------------------------------------
            # Tab 1: Audit History Timeline
            # -------------------------------------------------------------
            with tab_timeline:
                history = IssueService.get_issue_history(issue_id)
                if not history:
                    st.caption("No history events logged.")
                else:
                    for h in history:
                        c_t1, c_t2 = st.columns([1, 3])
                        with c_t1:
                            st.markdown(f"**{h['changed_at'].strftime('%d %b, %H:%M')}**")
                            st.caption(f"By: {h['changed_by_name'] or 'System'} ({h['changed_by_role'] or 'Auto'})")
                        with c_t2:
                            old_txt = f"{h['old_status']} ➔ " if h.get("old_status") else "Initial ➔ "
                            st.markdown(f"{render_status_badge(h['new_status'])} &nbsp; *{h['remarks'] or 'No remarks'}*", unsafe_allow_html=True)
                        st.markdown("<hr style='margin: 0.3rem 0; border: none; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)

            # -------------------------------------------------------------
            # Tab 2: Comments
            # -------------------------------------------------------------
            with tab_comments:
                comments = IssueService.get_issue_comments(issue_id)
                if comments:
                    for c in comments:
                        with st.chat_message(name=c["user_role"]):
                            st.markdown(f"**{c['user_name']}** ({c['user_role'].capitalize()}) • <span style='font-size:0.8rem; color:#64748B;'>{c['created_at'].strftime('%b %d, %H:%M')}</span>", unsafe_allow_html=True)
                            st.write(c["comment_text"])
                else:
                    st.caption("No comments posted yet.")

                with st.form(key=f"comment_form_{issue_id}", clear_on_submit=True):
                    new_comment = st.text_input("Add a comment / message for technicians", placeholder="Write message...")
                    if st.form_submit_button("Post Comment"):
                        if new_comment.strip():
                            succ, msg = IssueService.add_comment(issue_id, current_user["user_id"], new_comment)
                            if succ:
                                st.toast(msg, icon="💬")
                                st.rerun()
                            else:
                                st.error(msg)

            # -------------------------------------------------------------
            # Tab 3: Feedback
            # -------------------------------------------------------------
            with tab_feedback:
                existing_fb = IssueService.get_feedback(issue_id)

                if existing_fb:
                    st.info(f"⭐ **Your Feedback:** {existing_fb['rating']} / 5 Stars")
                    if existing_fb.get("feedback_text"):
                        st.write(f"*\"{existing_fb['feedback_text']}\"*")
                    st.caption(f"Submitted on {existing_fb['submitted_at'].strftime('%b %d, %Y')}")
                elif issue["status_name"] in ("resolved", "closed"):
                    st.markdown("#### Rate Resolution Quality")
                    with st.form(key=f"fb_form_{issue_id}", clear_on_submit=True):
                        rating = st.slider("Rating (1 = Poor, 5 = Excellent)", min_value=1, max_value=5, value=5)
                        fb_text = st.text_area("Remarks / Comments", placeholder="How satisfied are you with the resolution?")
                        if st.form_submit_button("Submit Rating & Feedback", type="primary"):
                            succ, msg = IssueService.submit_feedback(issue_id, current_user["user_id"], rating, fb_text)
                            if succ:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                else:
                    st.caption("Feedback can be submitted once this issue ticket is marked Resolved.")
