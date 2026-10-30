"""
Database Connection Manager and Context Utilities.
Provides robust thread-safe connection handling using mysql.connector and PyMySQL.
"""

import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from typing import Generator
from config import Config

# Connection pool for multi-page Streamlit concurrency
_connection_pool = None


def get_connection_pool():
    """Initializes or returns existing MySQL connection pool."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name="smart_campus_pool",
            pool_size=5,
            pool_reset_session=True,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
        )
    return _connection_pool


def get_raw_connection():
    """Gets a raw connection directly from config (or pool)."""
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False,
    )


@contextmanager
def get_db_cursor(commit: bool = False, dictionary: bool = True) -> Generator:
    """
    Context manager providing a managed database cursor with automatic cleanup.
    Usage:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(...)
    """
    conn = get_raw_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


@contextmanager
def get_transaction() -> Generator:
    """
    Context manager providing an explicit transactional connection.
    Automatically rolls back on exception and commits on clean block exit.
    Usage:
        with get_transaction() as (conn, cursor):
            cursor.execute(...)
    """
    conn = get_raw_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        yield (conn, cursor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
