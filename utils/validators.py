"""
Input validation utilities for Smart Campus System.
Enforces business rules and prevents invalid data inputs before database writes.
"""

import re
from typing import Tuple, Optional


def validate_email(email: str) -> bool:
    """Validates email format using regex."""
    if not email or len(email) > 150:
        return False
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def validate_issue_submission(
    title: str,
    description: str,
    category_id: Optional[int],
    location_id: Optional[int],
    priority_id: Optional[int],
) -> Tuple[bool, Optional[str]]:
    """
    Validates report issue form inputs.
    Returns (is_valid, error_message).
    """
    if not title or len(title.strip()) < 5:
        return False, "Issue title must be at least 5 characters long."
    if len(title.strip()) > 255:
        return False, "Issue title cannot exceed 255 characters."

    if not description or len(description.strip()) < 10:
        return False, "Please provide a detailed description (minimum 10 characters)."

    if not category_id:
        return False, "Please select a valid issue category."

    if not location_id:
        return False, "Please select the campus location."

    if not priority_id:
        return False, "Please select an urgency / priority level."

    return True, None


def validate_feedback(rating: int, feedback_text: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validates feedback rating (must be 1 to 5).
    """
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return False, "Feedback rating must be an integer between 1 and 5 stars."

    if feedback_text and len(feedback_text.strip()) > 1000:
        return False, "Feedback remarks cannot exceed 1000 characters."

    return True, None


def validate_file_upload(file_name: str, file_size_bytes: int, max_mb: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Validates uploaded attachment size and extension.
    Only allows images (.jpg, .jpeg, .png, .webp).
    """
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
    ext = "." + file_name.split(".")[-1].lower() if "." in file_name else ""

    if ext not in allowed_exts:
        return False, f"Invalid file type '{ext}'. Only images (JPG, PNG, WEBP) are accepted."

    max_bytes = max_mb * 1024 * 1024
    if file_size_bytes > max_bytes:
        return False, f"File exceeds maximum allowed size of {max_mb} MB."

    return True, None
