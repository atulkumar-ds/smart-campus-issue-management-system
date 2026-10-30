"""
Authentication and Authorization Module for Smart Campus System.
Handles bcrypt hashing, credential verification, and Streamlit session state guards.
"""

import bcrypt
import streamlit as st
from typing import Optional, Dict, Any, List
from db import get_db_cursor


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with random salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates a user against MySQL database.
    Verifies user exists, is_active is true, and bcrypt hash matches.
    Never trusts frontend claims.
    """
    if not email or not password:
        return None

    query = """
        SELECT 
            u.user_id,
            u.name,
            u.email,
            u.password_hash,
            u.phone,
            u.role,
            u.department_id,
            d.department_name,
            u.is_active
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.department_id
        WHERE LOWER(u.email) = LOWER(%s)
        LIMIT 1;
    """

    with get_db_cursor() as cursor:
        cursor.execute(query, (email.strip(),))
        user = cursor.fetchone()

    if not user:
        return None

    # Enforce active account check
    if not user.get("is_active"):
        return None

    # Verify bcrypt password
    if verify_password(password, user["password_hash"]):
        # Remove password hash before returning user object
        user.pop("password_hash", None)
        return user

    return None


def login_session(user: Dict[str, Any]) -> None:
    """Stores authenticated user in Streamlit session state."""
    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user["user_id"]
    st.session_state["user_name"] = user["name"]
    st.session_state["user_email"] = user["email"]
    st.session_state["user_role"] = user["role"]
    st.session_state["department_id"] = user.get("department_id")
    st.session_state["department_name"] = user.get("department_name")


def logout_session() -> None:
    """Clears authentication from session state."""
    keys_to_clear = [
        "authenticated",
        "user_id",
        "user_name",
        "user_email",
        "user_role",
        "department_id",
        "department_name",
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]


def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns currently authenticated user from session state if logged in."""
    if st.session_state.get("authenticated"):
        return {
            "user_id": st.session_state.get("user_id"),
            "name": st.session_state.get("user_name"),
            "email": st.session_state.get("user_email"),
            "role": st.session_state.get("user_role"),
            "department_id": st.session_state.get("department_id"),
            "department_name": st.session_state.get("department_name"),
        }
    return None


def require_role(allowed_roles: List[str]) -> Dict[str, Any]:
    """
    Page guard: Ensures user is authenticated and possesses one of the allowed roles.
    Stops page execution immediately if unauthorized.
    """
    user = get_current_user()

    if not user:
        st.warning("Please log in to access this page.")
        st.stop()

    if user["role"] not in allowed_roles:
        st.error(
            f"Access Denied: Your account role ({user['role']}) is not authorized to view this page."
        )
        st.stop()

    return user
