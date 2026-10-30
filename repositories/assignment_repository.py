"""
Assignment Repository for Database Access.
Handles manual assignments, auto-assignment via stored procedure,
and technician task status lifecycle.
"""

from typing import Optional, List, Dict, Any
from db import get_db_cursor, get_transaction


class AssignmentRepository:
    """Repository handling task assignments and technician workflow."""

    @staticmethod
    def assign_technician_manual(
        issue_id: int,
        technician_id: int,
        admin_id: int,
        remarks: Optional[str] = None,
    ) -> int:
        """
        Manually assigns a technician in an ACID transaction.
        Checks for duplicate active assignments, sets audit session variables,
        and lets trg_assignment_status transition issues.status_id to assigned.
        """
        with get_transaction() as (conn, cursor):
            # Check for existing active assignment
            cursor.execute(
                "SELECT COUNT(*) AS c FROM assignments WHERE issue_id = %s AND completed_at IS NULL;",
                (issue_id,),
            )
            if cursor.fetchone()["c"] > 0:
                raise ValueError("Issue already has an active technician assignment.")

            # Calculate expected SLA completion
            cursor.execute(
                """
                SELECT p.sla_hours 
                FROM priority_levels p
                JOIN issues i ON p.priority_id = i.priority_id
                WHERE i.issue_id = %s;
                """,
                (issue_id,),
            )
            row = cursor.fetchone()
            sla_hours = row["sla_hours"] if row else 24

            cursor.execute("SET @current_user_id = %s;", (admin_id,))
            cursor.execute(
                "SET @current_remarks = %s;",
                (remarks or f"Manually assigned to technician #{technician_id} by admin.",),
            )

            # Insert assignment; trigger updates issue status & logs history
            insert_sql = """
                INSERT INTO assignments (
                    issue_id, assigned_to, assigned_by, assigned_at, expected_completion
                ) VALUES (%s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL %s HOUR));
            """
            cursor.execute(insert_sql, (issue_id, technician_id, admin_id, sla_hours))
            return cursor.lastrowid

    @staticmethod
    def assign_technician_auto(issue_id: int, admin_id: int) -> int:
        """
        Executes stored procedure assign_least_loaded_technician.
        Returns the chosen technician_id.
        """
        conn = None
        try:
            from db import get_raw_connection
            conn = get_raw_connection()
            cursor = conn.cursor()
            res = cursor.callproc("assign_least_loaded_technician", [issue_id, admin_id, 0])
            conn.commit()
            cursor.close()
            chosen_tech_id = res[2]
            return chosen_tech_id
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_technician_tasks(technician_id: int, active_only: bool = False) -> List[Dict[str, Any]]:
        """Queries tasks assigned to a specific technician."""
        conditions = ["a.assigned_to = %s"]
        params = [technician_id]

        if active_only:
            conditions.append("a.completed_at IS NULL")
            conditions.append("s.status_name NOT IN ('resolved', 'closed', 'rejected')")

        sql = f"""
            SELECT 
                a.assignment_id,
                a.issue_id,
                a.assigned_at,
                a.expected_completion,
                a.completed_at,
                i.title,
                i.description,
                i.created_at AS issue_created_at,
                i.status_id,
                s.status_name,
                p.level_name AS priority_level,
                p.sla_hours,
                ic.category_name,
                d.department_name,
                loc.building_name,
                loc.floor,
                loc.room_number,
                u.name AS reporter_name,
                u.email AS reporter_email
            FROM assignments a
            JOIN issues i ON a.issue_id = i.issue_id
            JOIN issue_status s ON i.status_id = s.status_id
            JOIN priority_levels p ON i.priority_id = p.priority_id
            JOIN issue_categories ic ON i.category_id = ic.category_id
            JOIN departments d ON ic.default_department_id = d.department_id
            JOIN locations loc ON i.location_id = loc.location_id
            JOIN users u ON i.reported_by = u.user_id
            WHERE {' AND '.join(conditions)}
            ORDER BY a.assigned_at DESC;
        """
        with get_db_cursor() as cursor:
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()

    @staticmethod
    def resolve_task_by_technician(
        issue_id: int,
        technician_id: int,
        remarks: str,
    ) -> bool:
        """
        Marks an issue as resolved (status_id = 4) by technician.
        Updates assignment completed_at and sets audit variables.
        """
        with get_transaction() as (conn, cursor):
            # Verify assignment belongs to this technician
            cursor.execute(
                """
                SELECT assignment_id FROM assignments
                WHERE issue_id = %s AND assigned_to = %s AND completed_at IS NULL
                LIMIT 1;
                """,
                (issue_id, technician_id),
            )
            assignment = cursor.fetchone()
            if not assignment:
                raise ValueError("Active assignment not found for this technician on this issue.")

            assignment_id = assignment["assignment_id"]

            # 1. Set audit variables
            cursor.execute("SET @current_user_id = %s;", (technician_id,))
            cursor.execute("SET @current_remarks = %s;", (remarks or "Technician marked issue as resolved.",))

            # 2. Update issue to status_id = 4 ('resolved')
            # trg_issue_resolved_time will set resolved_at = NOW()
            # trg_issue_status_log will write history transition
            cursor.execute(
                "UPDATE issues SET status_id = 4 WHERE issue_id = %s;",
                (issue_id,),
            )

            # 3. Mark assignment completed
            cursor.execute(
                "UPDATE assignments SET completed_at = NOW() WHERE assignment_id = %s;",
                (assignment_id,),
            )

            return True

    @staticmethod
    def set_task_in_progress(
        issue_id: int,
        technician_id: int,
        remarks: Optional[str] = None,
    ) -> bool:
        """Transitions issue to in_progress (status_id = 3)."""
        with get_transaction() as (conn, cursor):
            cursor.execute("SET @current_user_id = %s;", (technician_id,))
            cursor.execute(
                "SET @current_remarks = %s;",
                (remarks or "Technician commenced work on site.",),
            )
            cursor.execute(
                "UPDATE issues SET status_id = 3 WHERE issue_id = %s;",
                (issue_id,),
            )
            return True

    @staticmethod
    def get_workload_view() -> List[Dict[str, Any]]:
        """Queries v_technician_workload view."""
        query = "SELECT * FROM v_technician_workload ORDER BY active_task_count ASC, technician_name ASC;"
        with get_db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
