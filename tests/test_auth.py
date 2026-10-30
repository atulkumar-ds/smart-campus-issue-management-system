"""
Automated tests for Authentication and User Verification.
"""

import pytest
from auth import authenticate_user, hash_password, verify_password


def test_bcrypt_hashing():
    """Verify bcrypt hash generation and verification."""
    password = "TestPassword@123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_admin_authentication():
    """Verify seeded admin can authenticate successfully."""
    user = authenticate_user("admin@campus.edu", "Password@123")
    assert user is not None
    assert user["role"] == "admin"
    assert user["email"] == "admin@campus.edu"
    assert "password_hash" not in user


def test_technician_authentication():
    """Verify seeded technician can authenticate."""
    user = authenticate_user("tech.electrical@campus.edu", "Password@123")
    assert user is not None
    assert user["role"] == "technician"
    assert user["department_name"] == "Electrical"


def test_student_authentication():
    """Verify seeded student can authenticate."""
    user = authenticate_user("aarav.sharma@campus.edu", "Password@123")
    assert user is not None
    assert user["role"] == "student"


def test_invalid_password_rejected():
    """Verify wrong password returns None."""
    user = authenticate_user("admin@campus.edu", "IncorrectPassword!")
    assert user is None


def test_nonexistent_email_rejected():
    """Verify non-existent user returns None."""
    user = authenticate_user("ghost.user@campus.edu", "Password@123")
    assert user is None


def test_empty_credentials_rejected():
    """Verify empty email/password returns None."""
    assert authenticate_user("", "") is None
    assert authenticate_user("admin@campus.edu", "") is None
