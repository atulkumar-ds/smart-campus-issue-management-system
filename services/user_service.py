"""
User Service Layer.
Business logic for user management and authentication.
"""

from typing import Optional, Dict, Any, List
from repositories.user_repository import UserRepository


class UserService:
    """Service handling user accounts and technician lookups."""

    @staticmethod
    def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
        return UserRepository.get_by_id(user_id)

    @staticmethod
    def get_technicians_for_department(department_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return UserRepository.get_technicians(department_id)
