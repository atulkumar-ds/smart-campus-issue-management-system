"""
UI Design System and Component Helpers for Streamlit.
Provides professional CSS styles, badges, metrics cards, and sidebar profile rendering.
"""

import streamlit as st
from auth import get_current_user, logout_session


STATUS_COLORS = {
    "open": ("#2563EB", "#DBEAFE"),          # Blue
    "assigned": ("#7C3AED", "#EDE9FE"),      # Purple
    "in_progress": ("#D97706", "#FEF3C7"),   # Orange / Amber
    "resolved": ("#059669", "#D1FAE5"),      # Green
    "closed": ("#4B5563", "#F3F4F6"),        # Grey
    "rejected": ("#DC2626", "#FEE2E2"),      # Red
}

PRIORITY_COLORS = {
    "Low": ("#2563EB", "#DBEAFE"),
    "Medium": ("#0D9488", "#CCFBF1"),
    "High": ("#D97706", "#FEF3C7"),
    "Critical": ("#DC2626", "#FEE2E2"),
}


def inject_custom_css():
    """Injects modern, SaaS-grade campus dashboard styles."""
    st.markdown(
        """
        <style>
        /* General page layout */
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* Metric cards */
        .metric-card {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 1.1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            margin-bottom: 0.8rem;
            text-align: left;
        }
        .metric-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.3rem;
        }
        .metric-value {
            font-size: 1.9rem;
            font-weight: 700;
            color: #111827;
        }

        /* Status & Priority Badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: capitalize;
            letter-spacing: 0.02em;
        }

        /* Custom alert box */
        .info-panel {
            background-color: #F8FAFC;
            border-left: 4px solid #2563EB;
            padding: 0.85rem 1.1rem;
            border-radius: 0 8px 8px 0;
            margin: 0.8rem 0;
            color: #1E293B;
            font-size: 0.92rem;
        }

        /* Sidebar profile styling */
        .sidebar-user {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            padding: 0.8rem;
            border-radius: 8px;
            margin-bottom: 1.2rem;
        }
        .sidebar-user-name {
            font-weight: 700;
            color: #1E293B;
            font-size: 0.95rem;
        }
        .sidebar-user-role {
            font-size: 0.8rem;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(status_name: str) -> str:
    """Returns HTML for a colored status badge."""
    text_color, bg_color = STATUS_COLORS.get(status_name.lower(), ("#374151", "#F3F4F6"))
    return f'<span class="badge" style="color: {text_color}; background-color: {bg_color};">{status_name.replace("_", " ")}</span>'


def render_priority_badge(priority_level: str) -> str:
    """Returns HTML for a colored priority badge."""
    text_color, bg_color = PRIORITY_COLORS.get(priority_level, ("#374151", "#F3F4F6"))
    return f'<span class="badge" style="color: {text_color}; background-color: {bg_color};">{priority_level}</span>'


def render_sidebar():
    """Renders persistent sidebar user info, navigation help, and logout button."""
    user = get_current_user()
    with st.sidebar:
        st.markdown("### 🏛️ Smart Campus")
        st.caption("AI-Powered Issue Management System")
        st.divider()

        if user:
            role_badge_color = {
                "admin": "#DC2626",
                "technician": "#7C3AED",
                "student": "#2563EB",
                "staff": "#059669",
            }.get(user["role"], "#4B5563")

            st.markdown(
                f"""
                <div class="sidebar-user">
                    <div class="sidebar-user-name">{user['name']}</div>
                    <div class="sidebar-user-role" style="color:{role_badge_color}; font-weight:700;">● {user['role']}</div>
                    <div style="font-size:0.8rem; color:#64748B; margin-top:2px;">{user['email']}</div>
                    {f"<div style='font-size:0.78rem; color:#475569; margin-top:4px;'>Dept: {user['department_name']}</div>" if user.get('department_name') else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("🚪 Logout", use_container_width=True):
                logout_session()
                st.rerun()
        else:
            st.info("Please log in to submit or manage campus complaints.")

        st.divider()
        st.caption("B.Tech DBMS Project • MySQL 8.0 & Streamlit")
