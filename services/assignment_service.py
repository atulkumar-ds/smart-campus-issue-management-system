"""
Assignment Service Layer.
Encapsulates technician dispatching, auto-assignment via stored procedure,
and technician task resolution workflows.
"""

from typing import Optional, List, Dict, Any, Tuple
from repositories.assignment_repository import AssignmentRepository
from repositories.issue_repository import IssueRepository


class AssignmentService:
    """Service handling task assignment workflows."""

    @staticmethod
    def assign_manual(
        issue_id: int,
        technician_id: int,
        admin_id: int,
        remarks: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Manually dispatches an issue to a technician."""
        try:
            AssignmentRepository.assign_technician_manual(
                issue_id=issue_id,
                technician_id=technician_id,
                admin_id=admin_id,
                remarks=remarks,
            )
            return True, f"Issue #{issue_id} successfully assigned to technician #{technician_id}."
        except ValueError as ve:
            return False, str(ve)
        except Exception as e:
            return False, f"Assignment transaction failed: {str(e)}"

    @staticmethod
    def assign_auto(issue_id: int, admin_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Executes stored procedure assign_least_loaded_technician.
        Returns (success, message, chosen_technician_id).
        """
        try:
            chosen_tech_id = AssignmentRepository.assign_technician_auto(issue_id, admin_id)
            return (
                True,
                f"Auto-assigned to least-loaded technician (ID #{chosen_tech_id}) via stored procedure.",
                chosen_tech_id,
            )
        except Exception as e:
            err_msg = str(e)
            if "Validation Error:" in err_msg or "Unauthorized:" in err_msg or "Assignment Error:" in err_msg:
                # Clean up MySQL error wrapping
                cleaned = err_msg.split(":")[-1].strip() if ":" in err_msg else err_msg
                return False, cleaned, None
            return False, f"Auto-assignment failed: {err_msg}", None

    @staticmethod
    def get_technician_tasks(technician_id: int, active_only: bool = False) -> List[Dict[str, Any]]:
        return AssignmentRepository.get_technician_tasks(technician_id, active_only)

    @staticmethod
    def set_in_progress(
        issue_id: int,
        technician_id: int,
        remarks: Optional[str] = None,
    ) -> Tuple[bool, str]:
        try:
            AssignmentRepository.set_task_in_progress(issue_id, technician_id, remarks)
            return True, f"Issue #{issue_id} marked as In Progress."
        except Exception as e:
            return False, f"Failed to update progress: {str(e)}"

    @staticmethod
    def resolve_task(
        issue_id: int,
        technician_id: int,
        remarks: str,
    ) -> Tuple[bool, str]:
        if not remarks or len(remarks.strip()) < 5:
            return False, "Please provide detailed resolution remarks (at least 5 characters)."

        try:
            AssignmentRepository.resolve_task_by_technician(issue_id, technician_id, remarks)
            return True, f"Issue #{issue_id} successfully marked as Resolved."
        except ValueError as ve:
            return False, str(ve)
        except Exception as e:
            return False, f"Resolution transaction failed: {str(e)}"

    @staticmethod
    def get_workload_summary() -> List[Dict[str, Any]]:
        return AssignmentRepository.get_workload_view()
