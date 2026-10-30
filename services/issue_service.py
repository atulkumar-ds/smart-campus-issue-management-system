"""
Issue Service Layer.
Encapsulates business rules for complaint submission, feedback, comments, and status transitions.
"""

from typing import Optional, List, Dict, Any, Tuple
from repositories.issue_repository import IssueRepository
from utils.validators import validate_issue_submission, validate_feedback


class IssueService:
    """Service handling campus complaint lifecycle."""

    @staticmethod
    def get_form_metadata() -> Dict[str, Any]:
        """Loads categories, locations, and priorities for the report issue form."""
        return {
            "categories": IssueRepository.get_categories(),
            "locations": IssueRepository.get_locations(),
            "priorities": IssueRepository.get_priority_levels(),
            "statuses": IssueRepository.get_issue_statuses(),
        }

    @staticmethod
    def report_issue(
        title: str,
        description: str,
        reported_by: int,
        category_id: int,
        location_id: int,
        priority_id: int,
        attachment_path: Optional[str] = None,
        attachment_type: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Validates inputs and creates a new issue in the database.
        Returns (success, message, issue_id).
        """
        # Validate inputs
        is_valid, error_msg = validate_issue_submission(
            title, description, category_id, location_id, priority_id
        )
        if not is_valid:
            return False, error_msg or "Validation failed.", None

        try:
            issue_id = IssueRepository.create_issue(
                title=title.strip(),
                description=description.strip(),
                reported_by=reported_by,
                category_id=category_id,
                location_id=location_id,
                priority_id=priority_id,
            )

            # Optional attachment
            if attachment_path and attachment_type:
                IssueRepository.create_attachment(
                    issue_id=issue_id,
                    file_path=attachment_path,
                    file_type=attachment_type,
                    uploaded_by=reported_by,
                )

            return True, f"Issue #{issue_id} submitted successfully!", issue_id
        except Exception as e:
            return False, f"Database error creating issue: {str(e)}", None

    @staticmethod
    def get_student_issues(user_id: int) -> List[Dict[str, Any]]:
        return IssueRepository.get_issues_by_reporter(user_id)

    @staticmethod
    def get_issue_details(issue_id: int) -> Optional[Dict[str, Any]]:
        return IssueRepository.get_issue_by_id(issue_id)

    @staticmethod
    def get_issue_history(issue_id: int) -> List[Dict[str, Any]]:
        return IssueRepository.get_issue_history(issue_id)

    @staticmethod
    def get_issue_comments(issue_id: int) -> List[Dict[str, Any]]:
        return IssueRepository.get_comments(issue_id)

    @staticmethod
    def add_comment(issue_id: int, user_id: int, comment_text: str) -> Tuple[bool, str]:
        if not comment_text or not comment_text.strip():
            return False, "Comment cannot be empty."
        try:
            IssueRepository.add_comment(issue_id, user_id, comment_text)
            return True, "Comment posted successfully."
        except Exception as e:
            return False, f"Failed to post comment: {str(e)}"

    @staticmethod
    def submit_feedback(
        issue_id: int,
        user_id: int,
        rating: int,
        feedback_text: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Submits reporter feedback for a resolved issue.
        Enforces:
        - Rating must be 1 to 5
        - Only the reporting user can submit feedback
        - Issue must be resolved or closed
        - Only one feedback per issue (UNIQUE constraint)
        """
        is_valid, err = validate_feedback(rating, feedback_text)
        if not is_valid:
            return False, err or "Invalid rating."

        issue = IssueRepository.get_issue_by_id(issue_id)
        if not issue:
            return False, "Issue not found."

        if issue["reporter_id"] != user_id:
            return False, "Unauthorized: Only the reporting student can submit feedback for this issue."

        if issue["status_name"] not in ("resolved", "closed"):
            return False, "Feedback can only be submitted after the issue is resolved or closed."

        # Check existing feedback
        existing_fb = IssueRepository.get_feedback(issue_id)
        if existing_fb:
            return False, "Feedback has already been submitted for this issue."

        try:
            IssueRepository.add_feedback(issue_id, user_id, rating, feedback_text)
            return True, "Thank you! Your feedback has been recorded."
        except Exception as e:
            return False, f"Database error submitting feedback: {str(e)}"

    @staticmethod
    def get_feedback(issue_id: int) -> Optional[Dict[str, Any]]:
        return IssueRepository.get_feedback(issue_id)

    @staticmethod
    def admin_update_status(
        issue_id: int,
        new_status_name: str,
        admin_id: int,
        remarks: str,
    ) -> Tuple[bool, str]:
        """Allows administrator to close or reject an issue."""
        statuses = {s["status_name"]: s["status_id"] for s in IssueRepository.get_issue_statuses()}
        new_status_id = statuses.get(new_status_name)
        if not new_status_id:
            return False, f"Invalid target status: '{new_status_name}'"

        try:
            IssueRepository.update_issue_status(issue_id, new_status_id, admin_id, remarks)
            return True, f"Issue #{issue_id} status updated to '{new_status_name}'."
        except Exception as e:
            return False, f"Error updating status: {str(e)}"
