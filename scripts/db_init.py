"""
Database Initialization Script for Smart Campus System.
Executes schema.sql and seed.sql against the configured MySQL 8.0 instance.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import Config
import mysql.connector


def run_sql_via_client(sql_file_path: Path) -> bool:
    """Executes a SQL file using mysql.exe or direct python queries."""
    mysql_bin_paths = [
        Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"),
        Path("mysql"),
    ]

    mysql_exe = None
    for p in mysql_bin_paths:
        try:
            res = subprocess.run(
                [str(p), "--version"],
                capture_output=True,
                text=True,
                shell=True if isinstance(p, str) else False,
            )
            if res.returncode == 0:
                mysql_exe = str(p)
                break
        except Exception:
            continue

    if mysql_exe:
        cmd = [
            mysql_exe,
            f"-h{Config.DB_HOST}",
            f"-P{Config.DB_PORT}",
            f"-u{Config.DB_USER}",
            f"-p{Config.DB_PASSWORD}",
            Config.DB_NAME,
            "-e",
            f"source {sql_file_path.as_posix()}",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error executing {sql_file_path.name} via mysql.exe: {res.stderr}")
            return False
        return True
    else:
        # Fallback to python connector statement-by-statement
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
        )
        cursor = conn.cursor()
        with open(sql_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        import re

        statements = re.split(r";\s*(?=(?:[^']*'[^']*')*[^']*$)", content)
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--") and not stmt.startswith("/*"):
                cursor.execute(stmt)
        conn.commit()
        cursor.close()
        conn.close()
        return True


def init_database():
    """Initializes smart_campus database, schema, and seed data."""
    print("Connecting to MySQL server...")
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
        )
        cursor = conn.cursor()

        print(f"Ensuring database `{Config.DB_NAME}` exists...")
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        conn.commit()
        cursor.close()
        conn.close()

        schema_path = Config.BASE_DIR / "sql" / "schema.sql"
        print(f"Applying {schema_path.name}...")
        if not run_sql_via_client(schema_path):
            return False

        seed_path = Config.BASE_DIR / "sql" / "seed.sql"
        print(f"Applying {seed_path.name}...")
        if not run_sql_via_client(seed_path):
            return False

        proc_path = Config.BASE_DIR / "sql" / "triggers_views_procs.sql"
        print(f"Applying {proc_path.name}...")
        if not run_sql_via_client(proc_path):
            return False

        # Verify
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nSuccessfully verified {len(tables)} tables in `{Config.DB_NAME}`:")
        for t in sorted(tables):
            print(f" - {t}")

        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role;")
        user_counts = cursor.fetchall()
        print("\nSeeded Users by Role:")
        for role, count in user_counts:
            print(f" - {role}: {count}")

        cursor.close()
        conn.close()
        print("\nDatabase initialization completed successfully!")
        return True

    except Exception as err:
        print(f"Initialization Error: {err}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
