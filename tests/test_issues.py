"""
Automated tests for Issue Service, Reporting, and Feedback Workflows.
"""

import pytest
from services.issue_service import IssueService
from repositories.issue_repository import IssueRepository
from db import get_db_cursor


def test_issue_submission_and_retrieval():
    """Verify valid issue submission creates issue and initial history row."""
    success, msg, issue_id = IssueService.report_issue(
        title="Fluorescent Light Broken LH-101",
        description="Flickering light near the blackboard causing eye strain.",
        reported_by=101,  # Aarav Sharma
        category_id=1,    # Electrical
        location_id=1,    # LH-101
        priority_id=2,    # Medium
    )
    assert success is True
    assert issue_id is not None

    # Retrieve issue details
    details = IssueService.get_issue_details(issue_id)
    assert details is not None
    assert details["title"] == "Fluorescent Light Broken LH-101"
    assert details["status_name"] == "open"
    assert details["reporter_name"] == "Aarav Sharma"
    assert details["department_name"] == "Electrical"

    # Verify initial history
    history = IssueService.get_issue_history(issue_id)
    assert len(history) >= 1
    assert history[0]["new_status"] == "open"

    # Cleanup
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM issues WHERE issue_id = %s;", (issue_id,))


def test_invalid_issue_validation():
    """Verify empty/short inputs are rejected."""
    success, msg, issue_id = IssueService.report_issue(
        title="Bad",  # < 5 chars
        description="Too short",  # < 10 chars
        reported_by=101,
        category_id=1,
        location_id=1,
        priority_id=2,
    )
    assert success is False
    assert issue_id is None
    assert "at least 5 characters" in msg


def test_feedback_submission_and_duplicate_prevention():
    """Verify feedback rating 1-5, reporter check, and unique constraint."""
    # 1. Create and resolve an issue
    _, _, issue_id = IssueService.report_issue(
        title="Washroom tap broken",
        description="Continuous water leak in second floor washroom.",
        reported_by=102,  # Aditi Rao
        category_id=2,    # Plumbing
        location_id=11,
        priority_id=2,
    )

    # Move to resolved status
    IssueService.admin_update_status(issue_id, "resolved", admin_id=1, remarks="Resolved by team.")

    # 2. Invalid rating (> 5)
    success, err = IssueService.submit_feedback(issue_id, user_id=102, rating=6, feedback_text="Too high")
    assert success is False

    # 3. Unauthorized user (not the reporter)
    success, err = IssueService.submit_feedback(issue_id, user_id=103, rating=5, feedback_text="Wrong user")
    assert success is False
    assert "Unauthorized" in err

    # 4. Valid feedback
    success, msg = IssueService.submit_feedback(issue_id, user_id=102, rating=5, feedback_text="Great fix!")
    assert success is True

    # 5. Duplicate feedback on same issue must be rejected
    success, err = IssueService.submit_feedback(issue_id, user_id=102, rating=4, feedback_text="Duplicate!")
    assert success is False
    assert "already been submitted" in err

    # Cleanup
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM issues WHERE issue_id = %s;", (issue_id,))
