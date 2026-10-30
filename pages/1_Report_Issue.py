"""
Student / Staff Issue Reporting Portal.
Includes AI-assisted title and category recommendation, dynamic department lookup,
and image attachment upload.
"""

import streamlit as st
from auth import require_role
from services.issue_service import IssueService
from ai.suggest import suggest_issue_details
from utils.file_handler import save_uploaded_attachment
from utils.ui_helpers import inject_custom_css, render_sidebar

st.set_page_config(page_title="Report Campus Issue • Smart Campus", page_icon="📝", layout="wide")
inject_custom_css()
render_sidebar()

# Role Protection: Only Students and Staff can report issues
current_user = require_role(["student", "staff"])

st.markdown("## 📝 Report a Campus Maintenance Issue")
st.caption("Provide details of the problem. You can use the AI Assistant to automatically suggest a title and category.")

# Load metadata from database
meta = IssueService.get_form_metadata()
categories = meta["categories"]
locations = meta["locations"]
priorities = meta["priorities"]

cat_id_to_dept = {c["category_id"]: c["department_name"] for c in categories}
cat_name_to_id = {c["category_name"]: c["category_id"] for c in categories}
cat_id_to_name = {c["category_id"]: c["category_name"] for c in categories}
cat_names = [c["category_name"] for c in categories]

# Session state initialization for AI suggestions
if "ai_title" not in st.session_state:
    st.session_state["ai_title"] = ""
if "ai_category_index" not in st.session_state:
    st.session_state["ai_category_index"] = 0

with st.container(border=True):
    st.markdown("### 1. Describe the Problem")
    description = st.text_area(
        "Problem Description *",
        placeholder="e.g. The ceiling fan in LH-101 is wobbling at high speed and making a loud rattling noise...",
        height=120,
        help="Please enter at least 10 characters detailing the maintenance or repair issue.",
    )

    c_btn, c_info = st.columns([1, 4])
    with c_btn:
        suggest_clicked = st.button("✨ AI Suggest", use_container_width=True, type="secondary")

    if suggest_clicked:
        if not description or len(description.strip()) < 10:
            st.warning("Please enter a descriptive problem description (at least 10 characters) first.")
        else:
            with st.spinner("Analyzing problem with AI Assistant..."):
                ai_res = suggest_issue_details(description)
                if ai_res["success"]:
                    st.session_state["ai_title"] = ai_res["title"]
                    cat_name = ai_res["category_name"]
                    if cat_name in cat_names:
                        st.session_state["ai_category_index"] = cat_names.index(cat_name)
                    st.toast("AI suggestions populated!", icon="✨")
                    st.success(f"{ai_res['message']} Title: **{ai_res['title']}** | Category: **{ai_res['category_name']}**")
                else:
                    st.info("Suggestion unavailable, please fill the form manually.")

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### 2. Issue Classification & Location")

    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input(
            "Issue Title *",
            value=st.session_state.get("ai_title", ""),
            placeholder="e.g. Ceiling Fan Rattling Noise in LH-101",
            help="Short summary of the issue (5 to 255 characters).",
        )

        selected_cat_name = st.selectbox(
            "Category *",
            options=cat_names,
            index=st.session_state.get("ai_category_index", 0),
            help="Select the operational category for this issue.",
        )
        selected_cat_id = cat_name_to_id[selected_cat_name]

        # Derived Department: Automatically fetched from MySQL, strictly read-only
        responsible_dept = cat_id_to_dept.get(selected_cat_id, "Unknown")
        st.text_input(
            "Responsible Department (Auto-Derived from MySQL)",
            value=responsible_dept,
            disabled=True,
            help="Determined strictly by database category-to-department relationship.",
        )

    with c2:
        # Location selection
        location_labels = [
            f"{loc['building_name']} • Floor {loc['floor']} • Room {loc['room_number']} ({loc['location_type'].capitalize()})"
            for loc in locations
        ]
        loc_label_to_id = {
            f"{loc['building_name']} • Floor {loc['floor']} • Room {loc['room_number']} ({loc['location_type'].capitalize()})": loc["location_id"]
            for loc in locations
        }

        selected_loc_label = st.selectbox(
            "Campus Location *",
            options=location_labels,
            help="Select the exact building and room.",
        )
        selected_location_id = loc_label_to_id[selected_loc_label]

        # Priority selection
        priority_options = [
            f"{p['level_name']} (Target SLA: {p['sla_hours']} Hours)"
            for p in priorities
        ]
        p_opt_to_id = {
            f"{p['level_name']} (Target SLA: {p['sla_hours']} Hours)": p["priority_id"]
            for p in priorities
        }
        selected_priority_opt = st.selectbox(
            "Urgency / Priority *",
            options=priority_options,
            index=1 if len(priority_options) > 1 else 0,
        )
        selected_priority_id = p_opt_to_id[selected_priority_opt]

        # Optional file attachment
        uploaded_image = st.file_uploader(
            "Attach Image / Photo Evidence (Optional)",
            type=["png", "jpg", "jpeg", "webp"],
            help="Maximum size: 5MB. Accepted formats: JPG, PNG, WEBP.",
        )

    st.divider()

    submit_button = st.button("🚀 Submit Complaint Ticket", use_container_width=True, type="primary")

    if submit_button:
        attachment_path = None
        attachment_type = None

        if uploaded_image:
            with st.spinner("Uploading attachment..."):
                saved_ok, file_path_or_err, ftype = save_uploaded_attachment(uploaded_image)
                if not saved_ok:
                    st.error(f"Attachment Upload Error: {file_path_or_err}")
                    st.stop()
                attachment_path = file_path_or_err
                attachment_type = ftype

        with st.spinner("Submitting complaint to MySQL database..."):
            success, msg, issue_id = IssueService.report_issue(
                title=title,
                description=description,
                reported_by=current_user["user_id"],
                category_id=selected_cat_id,
                location_id=selected_location_id,
                priority_id=selected_priority_id,
                attachment_path=attachment_path,
                attachment_type=attachment_type,
            )

            if success:
                st.balloons()
                st.success(
                    f"🎉 **Complaint Successfully Registered!** Ticket **#{issue_id}** is now Open. "
                    f"You can monitor repair progress on the 'My Issues' page."
                )
                # Reset AI session state
                st.session_state["ai_title"] = ""
                st.session_state["ai_category_index"] = 0
            else:
                st.error(f"Submission Error: {msg}")
