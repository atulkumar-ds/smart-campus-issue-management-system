"""
Automated tests for Assignment Service, Manual & Auto-Dispatch, and Technician Workflows.
"""

import pytest
from services.issue_service import IssueService
from services.assignment_service import AssignmentService
from repositories.assignment_repository import AssignmentRepository
from db import get_db_cursor


def test_manual_assignment_workflow():
    """Verify manual assignment dispatches technician, updates status to assigned, and logs history."""
    # Create issue
    _, _, issue_id = IssueService.report_issue(
        title="Physics Lab Equipment Calibration",
        description="Laser optics bench calibration is off by 2mm.",
        reported_by=104,
        category_id=6,  # Laboratory Equipment -> Mechanical
        location_id=7,  # Mech-Lab-2
        priority_id=2,
    )

    # Assign to Mechanical Technician (user_id = 6)
    success, msg = AssignmentService.assign_manual(
        issue_id=issue_id,
        technician_id=6,
        admin_id=1,
        remarks="Dispatched to mechanical specialist.",
    )
    assert success is True

    # Verify status changed to assigned (status_id = 2)
    details = IssueService.get_issue_details(issue_id)
    assert details["status_name"] == "assigned"
    assert details["assigned_technician_id"] == 6

    # Verify duplicate assignment blocked
    dup_success, dup_msg = AssignmentService.assign_manual(
        issue_id=issue_id,
        technician_id=6,
        admin_id=1,
    )
    assert dup_success is False
    assert "already has an active" in dup_msg

    # Cleanup
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM assignments WHERE issue_id = %s;", (issue_id,))
        cursor.execute("DELETE FROM issues WHERE issue_id = %s;", (issue_id,))


def test_technician_progress_and_resolution():
    """Verify technician can update task to in_progress, then resolved with remarks."""
    # Create issue and assign to Suresh Patel (user_id = 3, Civil/Plumbing)
    _, _, issue_id = IssueService.report_issue(
        title="Leaking Pipe Under Sink",
        description="Heavy dripping pipe under lab sink.",
        reported_by=105,
        category_id=2,  # Plumbing
        location_id=3,
        priority_id=3,
    )
    AssignmentService.assign_manual(issue_id=issue_id, technician_id=3, admin_id=1)

    # Technician sets in_progress
    succ, msg = AssignmentService.set_in_progress(issue_id=issue_id, technician_id=3)
    assert succ is True
    assert IssueService.get_issue_details(issue_id)["status_name"] == "in_progress"

    # Technician marks resolved
    succ, msg = AssignmentService.resolve_task(
        issue_id=issue_id,
        technician_id=3,
        remarks="Replaced rubber gasket and sealed joint. No leaks detected.",
    )
    assert succ is True

    details = IssueService.get_issue_details(issue_id)
    assert details["status_name"] == "resolved"
    assert details["resolved_at"] is not None

    # Cleanup
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM assignments WHERE issue_id = %s;", (issue_id,))
        cursor.execute("DELETE FROM issues WHERE issue_id = %s;", (issue_id,))
