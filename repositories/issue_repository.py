"""
Issue Repository for Database Access.
Executes parameterized queries for issue creation, queries against views,
and transaction-safe status transitions.
"""

from typing import Optional, List, Dict, Any
from db import get_db_cursor, get_transaction


class IssueRepository:
    """Repository handling issues, categories, locations, history, comments, and feedback."""

    @staticmethod
    def get_categories() -> List[Dict[str, Any]]:
        """Returns all categories with responsible default department name."""
        query = """
            SELECT ic.category_id, ic.category_name, ic.description,
                   ic.default_department_id, d.department_name
            FROM issue_categories ic
            JOIN departments d ON ic.default_department_id = d.department_id
            ORDER BY ic.category_name ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT ic.category_id, ic.category_name, ic.description,
                   ic.default_department_id, d.department_name
            FROM issue_categories ic
            JOIN departments d ON ic.default_department_id = d.department_id
            WHERE ic.category_id = %s;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (category_id,))
            return cursor.fetchone()

    @staticmethod
    def get_locations() -> List[Dict[str, Any]]:
        query = """
            SELECT location_id, building_name, floor, room_number, location_type
            FROM locations
            ORDER BY building_name ASC, floor ASC, room_number ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def get_priority_levels() -> List[Dict[str, Any]]:
        query = """
            SELECT priority_id, level_name, sla_hours
            FROM priority_levels
            ORDER BY sla_hours ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def get_issue_statuses() -> List[Dict[str, Any]]:
        query = """
            SELECT status_id, status_name, description
            FROM issue_status
            ORDER BY status_id ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def create_issue(
        title: str,
        description: str,
        reported_by: int,
        category_id: int,
        location_id: int,
        priority_id: int,
    ) -> int:
        """
        Creates an issue with initial status 'open' (status_id = 1)
        and explicitly inserts the initial status history record in an ACID transaction.
        """
        with get_transaction() as (conn, cursor):
            insert_issue_sql = """
                INSERT INTO issues (
                    title, description, reported_by, category_id,
                    location_id, priority_id, status_id, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW());
            """
            cursor.execute(
                insert_issue_sql,
                (title, description, reported_by, category_id, location_id, priority_id),
            )
            issue_id = cursor.lastrowid

            # Section 3: Initial status must be logged in issue_status_history
            insert_history_sql = """
                INSERT INTO issue_status_history (
                    issue_id, old_status_id, new_status_id, changed_by, changed_at, remarks
                ) VALUES (%s, NULL, 1, %s, NOW(), 'Issue submitted by reporter.');
            """
            cursor.execute(insert_history_sql, (issue_id, reported_by))

            return issue_id

    @staticmethod
    def create_attachment(issue_id: int, file_path: str, file_type: str, uploaded_by: int) -> int:
        query = """
            INSERT INTO attachments (issue_id, file_path, file_type, uploaded_by, uploaded_at)
            VALUES (%s, %s, %s, %s, NOW());
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (issue_id, file_path, file_type, uploaded_by))
            return cursor.lastrowid

    @staticmethod
    def get_issue_by_id(issue_id: int) -> Optional[Dict[str, Any]]:
        """Queries comprehensive v_issue_details view for single issue."""
        query = "SELECT * FROM v_issue_details WHERE issue_id = %s;"
        with get_db_cursor() as cursor:
            cursor.execute(query, (issue_id,))
            return cursor.fetchone()

    @staticmethod
    def get_issues_by_reporter(user_id: int) -> List[Dict[str, Any]]:
        """Queries issues reported by a specific user."""
        query = """
            SELECT * FROM v_issue_details
            WHERE reporter_id = %s
            ORDER BY created_at DESC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_all_issues(
        status_id: Optional[int] = None,
        category_id: Optional[int] = None,
        building_name: Optional[str] = None,
        priority_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Queries v_issue_details view with optional filters and search."""
        conditions = ["1=1"]
        params = []

        if status_id:
            conditions.append("status_id = %s")
            params.append(status_id)

        if category_id:
            conditions.append("category_id = %s")
            params.append(category_id)

        if building_name and building_name != "All Buildings":
            conditions.append("building_name = %s")
            params.append(building_name)

        if priority_id:
            conditions.append("priority_id = %s")
            params.append(priority_id)

        if search_query:
            term = f"%{search_query.strip()}%"
            conditions.append("(title LIKE %s OR description LIKE %s OR reporter_name LIKE %s)")
            params.extend([term, term, term])

        sql = f"""
            SELECT * FROM v_issue_details
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()

    @staticmethod
    def get_issue_history(issue_id: int) -> List[Dict[str, Any]]:
        """Retrieves full status transition history timeline."""
        query = """
            SELECT 
                h.history_id,
                h.issue_id,
                h.old_status_id,
                old_s.status_name AS old_status,
                h.new_status_id,
                new_s.status_name AS new_status,
                h.changed_by,
                u.name AS changed_by_name,
                u.role AS changed_by_role,
                h.changed_at,
                h.remarks
            FROM issue_status_history h
            LEFT JOIN issue_status old_s ON h.old_status_id = old_s.status_id
            JOIN issue_status new_s ON h.new_status_id = new_s.status_id
            LEFT JOIN users u ON h.changed_by = u.user_id
            WHERE h.issue_id = %s
            ORDER BY h.changed_at ASC, h.history_id ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (issue_id,))
            return cursor.fetchall()

    @staticmethod
    def get_comments(issue_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT c.comment_id, c.issue_id, c.user_id, u.name AS user_name,
                   u.role AS user_role, c.comment_text, c.created_at
            FROM comments c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.issue_id = %s
            ORDER BY c.created_at ASC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (issue_id,))
            return cursor.fetchall()

    @staticmethod
    def add_comment(issue_id: int, user_id: int, comment_text: str) -> int:
        query = """
            INSERT INTO comments (issue_id, user_id, comment_text, created_at)
            VALUES (%s, %s, %s, NOW());
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (issue_id, user_id, comment_text.strip()))
            return cursor.lastrowid

    @staticmethod
    def add_feedback(issue_id: int, user_id: int, rating: int, feedback_text: Optional[str]) -> int:
        """Submits feedback for a resolved issue. Enforces UNIQUE issue_id."""
        query = """
            INSERT INTO feedback (issue_id, user_id, rating, feedback_text, submitted_at)
            VALUES (%s, %s, %s, %s, NOW());
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (issue_id, user_id, rating, feedback_text.strip() if feedback_text else None))
            return cursor.lastrowid

    @staticmethod
    def get_feedback(issue_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT f.feedback_id, f.issue_id, f.user_id, u.name AS user_name,
                   f.rating, f.feedback_text, f.submitted_at
            FROM feedback f
            JOIN users u ON f.user_id = u.user_id
            WHERE f.issue_id = %s;
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (issue_id,))
            return cursor.fetchone()

    @staticmethod
    def update_issue_status(
        issue_id: int,
        new_status_id: int,
        changed_by: int,
        remarks: Optional[str] = None,
    ) -> bool:
        """
        Updates issue status. Sets MySQL session variables so trg_issue_status_log
        captures the actor and remarks automatically.
        """
        with get_transaction() as (conn, cursor):
            cursor.execute("SET @current_user_id = %s;", (changed_by,))
            cursor.execute("SET @current_remarks = %s;", (remarks or "Status updated via application.",))
            cursor.execute(
                "UPDATE issues SET status_id = %s, updated_at = NOW() WHERE issue_id = %s;",
                (new_status_id, issue_id),
            )
            return True
