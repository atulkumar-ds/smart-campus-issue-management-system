"""
User Repository for Database Access.
Handles parameterized queries for user retrieval and technician lookups.
"""

from typing import Optional, List, Dict, Any
from db import get_db_cursor


class UserRepository:
    """Repository handling users table queries."""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT u.user_id, u.name, u.email, u.phone, u.role, u.department_id,
                   d.department_name, u.is_active, u.created_at
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE u.user_id = %s;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchone()

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT u.user_id, u.name, u.email, u.phone, u.role, u.department_id,
                   d.department_name, u.is_active, u.created_at
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE LOWER(u.email) = LOWER(%s);
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (email.strip(),))
            return cursor.fetchone()

    @staticmethod
    def get_technicians(department_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves active technicians, optionally filtered by department."""
        if department_id:
            query = """
                SELECT u.user_id, u.name, u.email, u.phone, u.role, u.department_id,
                       d.department_name
                FROM users u
                JOIN departments d ON u.department_id = d.department_id
                WHERE u.role = 'technician' AND u.is_active = TRUE AND u.department_id = %s
                ORDER BY u.name ASC;
            """
            params = (department_id,)
        else:
            query = """
                SELECT u.user_id, u.name, u.email, u.phone, u.role, u.department_id,
                       d.department_name
                FROM users u
                JOIN departments d ON u.department_id = d.department_id
                WHERE u.role = 'technician' AND u.is_active = TRUE
                ORDER BY d.department_name ASC, u.name ASC;
            """
            params = ()

        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
