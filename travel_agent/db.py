"""SQLite storage for saved trips.

One normalised ``trips`` table keeps the searchable columns; the full plan is
stored as JSON so a saved trip can be reopened exactly as it was generated.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS trips (
    trip_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT    NOT NULL,
    origin        TEXT    NOT NULL,
    destination   TEXT    NOT NULL,
    start_date    TEXT    NOT NULL,
    trip_days     INTEGER NOT NULL,
    travelers     INTEGER NOT NULL,
    total_cost    INTEGER NOT NULL,
    engine_mode   TEXT    NOT NULL,
    plan_json     TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trips_created_at ON trips (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trips_destination ON trips (destination);
"""


@contextmanager
def _connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(SCHEMA)
        yield connection
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def save_trip(plan: dict) -> int:
    request = plan["request"]
    with _connect() as db:
        cursor = db.execute(
            "INSERT INTO trips (created_at, origin, destination, start_date, trip_days, travelers, total_cost, engine_mode, plan_json)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                request["origin"], request["destination"], request["start_date"], request["days"],
                request["travelers"], plan["budget"]["total"], plan["engine"]["mode"],
                json.dumps(plan, default=str),
            ),
        )
        return cursor.lastrowid


def list_trips(limit: int = 50) -> list[dict]:
    with _connect() as db:
        rows = db.execute(
            "SELECT trip_id, created_at, origin, destination, start_date, trip_days, travelers, total_cost, engine_mode"
            " FROM trips ORDER BY created_at DESC, trip_id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def load_trip(trip_id: int) -> dict | None:
    with _connect() as db:
        row = db.execute("SELECT plan_json FROM trips WHERE trip_id = ?", (trip_id,)).fetchone()
    return json.loads(row["plan_json"]) if row else None


def delete_trip(trip_id: int) -> None:
    with _connect() as db:
        db.execute("DELETE FROM trips WHERE trip_id = ?", (trip_id,))
