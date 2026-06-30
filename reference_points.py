"""Persistência local de pontos de base de referência (SQLite)."""

import os
import sqlite3
from datetime import datetime


class ReferencePointStore:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reference_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    lat_gms TEXT NOT NULL,
                    lon_gms TEXT NOT NULL,
                    alt REAL NOT NULL,
                    obs_path TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def list_names(self):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT name FROM reference_points ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [row[0] for row in rows]

    def get(self, name):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT name, lat_gms, lon_gms, alt, obs_path, description
                FROM reference_points
                WHERE name = ?
                """,
                (name,),
            ).fetchone()
        if not row:
            return None
        return {
            "name": row[0],
            "lat_gms": row[1],
            "lon_gms": row[2],
            "alt": row[3],
            "obs_path": row[4] or "",
            "description": row[5] or "",
        }

    def save(self, name, lat_gms, lon_gms, alt, obs_path="", description=""):
        name = name.strip()
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reference_points
                    (name, lat_gms, lon_gms, alt, obs_path, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    lat_gms = excluded.lat_gms,
                    lon_gms = excluded.lon_gms,
                    alt = excluded.alt,
                    obs_path = excluded.obs_path,
                    description = excluded.description
                """,
                (
                    name,
                    lat_gms.strip(),
                    lon_gms.strip(),
                    float(alt),
                    obs_path.strip() or None,
                    description.strip() or None,
                    now,
                ),
            )

    def delete(self, name):
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM reference_points WHERE name = ?",
                (name,),
            )
        return cursor.rowcount > 0
