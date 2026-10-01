import sqlite3
from pathlib import Path


def init_db(db_path: str | Path) -> None:
    """Create the users table if it does not already exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)


def create_user(
    db_path: str | Path,
    username: str,
    password_hash: str
) -> int:
    """Save a new user and return their user ID."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        return cursor.lastrowid


def get_user(
    db_path: str | Path,
    username: str
) -> tuple[int, str] | None:
    """Find a user and return their ID and password hash."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return row[0], row[1]