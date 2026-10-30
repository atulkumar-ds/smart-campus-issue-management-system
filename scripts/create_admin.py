"""
CLI Utility to create an administrative user in MySQL.
Prompts for name, email, and password, hashes using bcrypt, and writes to MySQL.
"""

import sys
from pathlib import Path
import getpass

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Config
from auth import hash_password
from db import get_db_cursor


def create_admin():
    print("=" * 50)
    print("Smart Campus - Admin Account Creator")
    print("=" * 50)

    name = input("Enter Admin Full Name: ").strip()
    email = input("Enter Admin Email: ").strip()
    if not name or not email:
        print("Error: Name and Email are required.")
        return False

    password = getpass.getpass("Enter Admin Password: ")
    confirm = getpass.getpass("Confirm Admin Password: ")

    if password != confirm:
        print("Error: Passwords do not match.")
        return False

    if len(password) < 6:
        print("Error: Password must be at least 6 characters long.")
        return False

    pwd_hash = hash_password(password)

    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if email exists
            cursor.execute("SELECT user_id FROM users WHERE LOWER(email) = LOWER(%s);", (email,))
            if cursor.fetchone():
                print(f"Error: User with email '{email}' already exists.")
                return False

            query = """
                INSERT INTO users (name, email, password_hash, role, department_id, is_active, created_at)
                VALUES (%s, %s, %s, 'admin', 6, TRUE, NOW());
            """
            cursor.execute(query, (name, email, pwd_hash))
            admin_id = cursor.lastrowid
            print(f"SUCCESS: Administrator '{name}' (ID #{admin_id}) created successfully!")
            return True
    except Exception as e:
        print(f"Database Error: {e}")
        return False


if __name__ == "__main__":
    create_admin()
