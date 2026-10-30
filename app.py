"""
Smart Campus Issue Management System - Streamlit Entry Point.
Provides authentication gateway, session state initialization, and role-based portal routing.
"""

import streamlit as st
from config import Config
from auth import (
    authenticate_user,
    login_session,
    logout_session,
    get_current_user,
)
from utils.ui_helpers import inject_custom_css, render_sidebar

# Configure Page
st.set_page_config(
    page_title="Smart Campus • Issue Management",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system styles
inject_custom_css()
render_sidebar()

user = get_current_user()

if not user:
    # -------------------------------------------------------------
    # LOGIN SCREEN
    # -------------------------------------------------------------
    st.markdown(
        """
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 2rem;">
            <h1 style="color: #1E3A8A; font-size: 2.3rem; margin-bottom: 0.3rem;">🏛️ Smart Campus Issue Management System</h1>
            <p style="color: #64748B; font-size: 1.05rem;">AI-Powered Centralized Facility Incident Reporting & SLA Tracking</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        with st.container(border=True):
            st.markdown("#### 🔐 Sign In to Campus Portal")
            st.caption("Enter your institutional email and password to continue.")

            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Institutional Email", placeholder="e.g. admin@campus.edu")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if submitted:
                    if not email or not password:
                        st.error("Please provide both email and password.")
                    else:
                        with st.spinner("Authenticating with database..."):
                            auth_user = authenticate_user(email.strip(), password)
                            if auth_user:
                                login_session(auth_user)
                                st.success(f"Welcome back, {auth_user['name']}!")
                                st.rerun()
                            else:
                                st.error("Invalid email, password, or account is deactivated.")

        # Demo Credentials Accordion
        with st.expander("📋 Click to View Demo Accounts & Credentials"):
            st.markdown(
                """
                | Role | Email | Password |
                |---|---|---|
                | **Campus Admin** | `admin@campus.edu` | `Password@123` |
                | **Technician (Electrical)** | `tech.electrical@campus.edu` | `Password@123` |
                | **Technician (Civil & Plumbing)** | `tech.civil@campus.edu` | `Password@123` |
                | **Technician (IT & Network)** | `tech.network@campus.edu` | `Password@123` |
                | **Student** | `aarav.sharma@campus.edu` | `Password@123` |
                | **Student** | `aditi.rao@campus.edu` | `Password@123` |
                """
            )

else:
    # -------------------------------------------------------------
    # AUTHENTICATED WELCOME / GATEWAY SCREEN
    # -------------------------------------------------------------
    st.markdown(f"## Welcome, {user['name']} 👋")
    st.caption(f"Role: **{user['role'].upper()}** • Institutional ID #{user['user_id']}")

    st.markdown(
        """
        <div class="info-panel">
            <b>Campus Issue Tracking System:</b> Use the left navigation sidebar to access your authorized portals.
            All complaint logs, status history, SLA tracking, and technician assignments are actively audited in MySQL 8.0.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📌 Quick Navigation")

    if user["role"] in ("student", "staff"):
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("#### 📝 Report Campus Issue")
                st.write("Submit facility complaints with AI-assisted title and category classification.")
                st.page_link("pages/1_Report_Issue.py", label="Go to Report Issue", icon="✍️")
        with c2:
            with st.container(border=True):
                st.markdown("#### 📂 My Reported Issues")
                st.write("Track resolution timeline, chat with technicians, and provide post-repair feedback.")
                st.page_link("pages/2_My_Issues.py", label="View My Issues", icon="📋")

    elif user["role"] == "admin":
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("#### 📊 Operations Dashboard")
                st.write("Live KPI cards, SLA breach alerts, and interactive Plotly facility breakdown charts.")
                st.page_link("pages/3_Admin_Dashboard.py", label="Open Analytics Dashboard", icon="📈")
        with c2:
            with st.container(border=True):
                st.markdown("#### ⚙️ Manage Campus Issues")
                st.write("Review all complaints, manual technician assignment, and auto-dispatch via MySQL stored procedure.")
                st.page_link("pages/4_Manage_Issues.py", label="Manage Issues", icon="🛠️")

    elif user["role"] == "technician":
        with st.container(border=True):
            st.markdown("#### 🔧 Technician Work Orders")
            st.write(f"Access maintenance tasks assigned to you in the **{user.get('department_name', 'Campus')}** department.")
            st.page_link("pages/5_Technician_Tasks.py", label="Go to My Tasks", icon="⚡")
