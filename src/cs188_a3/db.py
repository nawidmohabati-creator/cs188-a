import sqlite3
from pathlib import Path


def init_db(db_path: str | Path) -> None:
    """Create the users and trips tables if they do not already exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                city TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                budget REAL NOT NULL,
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id)
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


def create_trip(
    db_path: str | Path,
    owner_id: int,
    city: str,
    start_date: str,
    end_date: str,
    budget: float,
    notes: str,
) -> int:
    """Create a trip and return its ID."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO trips
            (owner_id, city, start_date, end_date, budget, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (owner_id, city, start_date, end_date, budget, notes),
        )
        return cursor.lastrowid


def get_trips(
    db_path: str | Path,
    city: str | None = None,
) -> list[dict]:
    """Return all trips, optionally filtered by city."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        if city is None:
            cursor = conn.execute(
                """
                SELECT id, city, start_date, end_date, budget, notes, created_at
                FROM trips
                ORDER BY id
                """
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, city, start_date, end_date, budget, notes, created_at
                FROM trips
                WHERE city = ?
                ORDER BY id
                """,
                (city,),
            )

        return [dict(row) for row in cursor.fetchall()]


def get_trip(db_path: str | Path, trip_id: int) -> dict | None:
    """Return one trip by its ID, or None if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT id, owner_id, city, start_date, end_date,
                   budget, notes, created_at
            FROM trips
            WHERE id = ?
            """,
            (trip_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)


def update_trip(
    db_path: str | Path,
    trip_id: int,
    changes: dict,
) -> None:
    """Update the provided fields for one trip."""
    with sqlite3.connect(db_path) as conn:
        # It updates only the fields that were included in the PATCH request.
        if "city" in changes:
            conn.execute(
                "UPDATE trips SET city = ? WHERE id = ?",
                (changes["city"], trip_id),
            )

        if "start_date" in changes:
            conn.execute(
                "UPDATE trips SET start_date = ? WHERE id = ?",
                (changes["start_date"], trip_id),
            )

        if "end_date" in changes:
            conn.execute(
                "UPDATE trips SET end_date = ? WHERE id = ?",
                (changes["end_date"], trip_id),
            )

        if "budget" in changes:
            conn.execute(
                "UPDATE trips SET budget = ? WHERE id = ?",
                (changes["budget"], trip_id),
            )

        if "notes" in changes:
            conn.execute(
                "UPDATE trips SET notes = ? WHERE id = ?",
                (changes["notes"], trip_id),
            )

            

def delete_trip(db_path: str | Path, trip_id: int) -> None:
    """Delete one trip by its ID."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "DELETE FROM trips WHERE id = ?",
            (trip_id,),
        )