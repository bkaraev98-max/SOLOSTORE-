import sqlite3
from pathlib import Path

from config import DATABASE_PATH


class Database:
    def __init__(self, path: str = DATABASE_PATH):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA journal_mode=WAL;"
        )

        connection.execute(
            "PRAGMA foreign_keys=ON;"
        )

        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    role TEXT NOT NULL DEFAULT 'USER',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_telegram_id INTEGER,
                    action TEXT NOT NULL,
                    target_type TEXT,
                    target_id TEXT,
                    details TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def upsert_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        role: str = "USER",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    telegram_id,
                    username,
                    first_name,
                    role
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id)
                DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    telegram_id,
                    username,
                    first_name,
                    role,
                ),
            )

    def get_user(self, telegram_id: int):
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM users
                WHERE telegram_id = ?
                """,
                (telegram_id,),
            ).fetchone()

    def add_audit_log(
        self,
        actor_telegram_id: int | None,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        details: str | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_logs (
                    actor_telegram_id,
                    action,
                    target_type,
                    target_id,
                    details
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    actor_telegram_id,
                    action,
                    target_type,
                    target_id,
                    details,
                ),
      )
