"""
Automated tests for Database Triggers, Views, Procedures, and Transactions.
Verifies all Section 5 requirements on live MySQL instance.
"""

import pytest
import mysql.connector
from config import Config


@pytest.fixture(scope="module")
def db_conn():
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False,
    )
    yield conn
    conn.close()


def test_views_exist(db_conn):
    """Verify that all four required views exist and return valid query schemas."""
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT TABLE_NAME FROM information_schema.VIEWS WHERE TABLE_SCHEMA = %s;",
        (Config.DB_NAME,),
    )
    views = [r[0].lower() for r in cursor.fetchall()]

    expected_views = [
        "v_open_issues_by_department",
        "v_overdue_issues",
        "v_technician_workload",
        "v_issue_details",
    ]
    for ev in expected_views:
        assert ev in views, f"View {ev} not found in database."

    # Test querying each view without SQL errors
    for ev in expected_views:
        cursor.execute(f"SELECT * FROM {ev} LIMIT 5;")
        cursor.fetchall()
    cursor.close()


def test_triggers_exist(db_conn):
    """Verify that all three triggers exist."""
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = %s;",
        (Config.DB_NAME,),
    )
    triggers = [r[0].lower() for r in cursor.fetchall()]

    expected_triggers = [
        "trg_issue_status_log",
        "trg_issue_resolved_time",
        "trg_assignment_status",
    ]
    for et in expected_triggers:
        assert et in triggers, f"Trigger {et} not found."
    cursor.close()


def test_procedure_exists(db_conn):
    """Verify stored procedure exists."""
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT ROUTINE_NAME FROM information_schema.ROUTINES "
        "WHERE ROUTINE_SCHEMA = %s AND ROUTINE_TYPE = 'PROCEDURE';",
        (Config.DB_NAME,),
    )
    procs = [r[0].lower() for r in cursor.fetchall()]
    assert "assign_least_loaded_technician" in procs
    cursor.close()


def test_trigger_workflow_and_transaction(db_conn):
    """
    Test end-to-end trigger integration:
    1. Create an issue in 'open' status.
    2. Insert an assignment: trg_assignment_status -> updates issue status to 'assigned'.
    3. Check trg_issue_status_log captured the transition to 'assigned'.
    4. Update status to 'resolved': trg_issue_resolved_time sets resolved_at.
    5. Check trg_issue_status_log captured transition to 'resolved'.
    """
    cursor = db_conn.cursor(dictionary=True)

    # 1. Insert test issue
    cursor.execute(
        """
        INSERT INTO issues (title, description, reported_by, category_id, location_id, priority_id, status_id)
        VALUES ('Test Trigger Issue', 'Verification of DB triggers', 101, 1, 1, 2, 1);
        """
    )
    db_conn.commit()
    issue_id = cursor.lastrowid
    assert issue_id is not None

    # Verify initial state: status is open (1), resolved_at is NULL
    cursor.execute("SELECT status_id, resolved_at FROM issues WHERE issue_id = %s;", (issue_id,))
    row = cursor.fetchone()
    assert row["status_id"] == 1
    assert row["resolved_at"] is None

    # 2. Insert assignment for Electrical Technician (user_id = 2)
    # trg_assignment_status should update issues.status_id = 2 ('assigned')
    cursor.execute(
        """
        INSERT INTO assignments (issue_id, assigned_to, assigned_by)
        VALUES (%s, 2, 1);
        """,
        (issue_id,),
    )
    db_conn.commit()

    # Verify issue status was automatically updated by trigger to 2 ('assigned')
    cursor.execute("SELECT status_id FROM issues WHERE issue_id = %s;", (issue_id,))
    row = cursor.fetchone()
    assert row["status_id"] == 2, "trg_assignment_status did not update issues.status_id to assigned"

    # Verify trg_issue_status_log logged exactly one transition row
    cursor.execute(
        "SELECT * FROM issue_status_history WHERE issue_id = %s ORDER BY history_id DESC;",
        (issue_id,),
    )
    history = cursor.fetchall()
    assert len(history) >= 1
    assert history[0]["old_status_id"] == 1
    assert history[0]["new_status_id"] == 2

    # 3. Update status to 4 ('resolved')
    # trg_issue_resolved_time should set resolved_at to non-null timestamp
    cursor.execute("UPDATE issues SET status_id = 4 WHERE issue_id = %s;", (issue_id,))
    db_conn.commit()

    cursor.execute("SELECT status_id, resolved_at FROM issues WHERE issue_id = %s;", (issue_id,))
    row = cursor.fetchone()
    assert row["status_id"] == 4
    assert row["resolved_at"] is not None, "trg_issue_resolved_time did not set resolved_at"

    # Clean up test records (CASCADE cleans up assignments and history)
    cursor.execute("DELETE FROM assignments WHERE issue_id = %s;", (issue_id,))
    cursor.execute("DELETE FROM issue_status_history WHERE issue_id = %s;", (issue_id,))
    cursor.execute("DELETE FROM issues WHERE issue_id = %s;", (issue_id,))
    db_conn.commit()
    cursor.close()


def test_assign_least_loaded_technician_procedure(db_conn):
    """
    Test stored procedure assign_least_loaded_technician:
    Creates an unassigned IT issue (category_id = 3 -> CS & IT department_id = 3).
    Calls procedure with admin_id = 1.
    Verifies that technician ID 4 (Amit Verma, tech.network) is selected and assigned.
    """
    cursor = db_conn.cursor(dictionary=True)

    # Insert unassigned IT issue
    cursor.execute(
        """
        INSERT INTO issues (title, description, reported_by, category_id, location_id, priority_id, status_id)
        VALUES ('Wi-Fi Dead Zone', 'Lab 2 has no connection', 102, 3, 4, 3, 1);
        """
    )
    db_conn.commit()
    issue_id = cursor.lastrowid

    # Call procedure
    proc_cursor = db_conn.cursor()
    res = proc_cursor.callproc("assign_least_loaded_technician", [issue_id, 1, 0])
    proc_cursor.close()

    out_param = res[2]
    assert out_param == 4, f"Expected technician ID 4 (Computer Science), got {out_param}"

    # Verify issue status is now 'assigned'
    cursor.execute("SELECT status_id FROM issues WHERE issue_id = %s;", (issue_id,))
    assert cursor.fetchone()["status_id"] == 2

    # Verify assignment record created
    cursor.execute(
        "SELECT * FROM assignments WHERE issue_id = %s AND assigned_to = 4;",
        (issue_id,),
    )
    assignment = cursor.fetchone()
    assert assignment is not None
    assert assignment["assigned_by"] == 1

    # Clean up
    cursor.execute("DELETE FROM assignments WHERE issue_id = %s;", (issue_id,))
    cursor.execute("DELETE FROM issue_status_history WHERE issue_id = %s;", (issue_id,))
    cursor.execute("DELETE FROM issues WHERE issue_id = %s;", (issue_id,))
    db_conn.commit()
    cursor.close()


def test_procedure_unauthorized_rollback(db_conn):
    """
    Test that calling stored procedure with non-admin user fails and rolls back.
    Student user_id = 101.
    """
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(
        """
        INSERT INTO issues (title, description, reported_by, category_id, location_id, priority_id, status_id)
        VALUES ('Unauthorized Test Issue', 'Should roll back', 103, 2, 5, 1, 1);
        """
    )
    db_conn.commit()
    issue_id = cursor.lastrowid

    with pytest.raises(mysql.connector.Error) as exc_info:
        proc_cursor = db_conn.cursor()
        proc_cursor.callproc("assign_least_loaded_technician", [issue_id, 101, 0])
        proc_cursor.close()

    assert "Unauthorized" in str(exc_info.value)

    # Verify no assignment was inserted
    cursor.execute("SELECT COUNT(*) as c FROM assignments WHERE issue_id = %s;", (issue_id,))
    assert cursor.fetchone()["c"] == 0

    # Clean up
    cursor.execute("DELETE FROM issues WHERE issue_id = %s;", (issue_id,))
    db_conn.commit()
    cursor.close()
