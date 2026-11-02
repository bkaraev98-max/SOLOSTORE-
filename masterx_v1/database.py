
"""
MASTER X — Version 1.0
Central SQLite database.

MASTER X is a marketplace/database intermediary.
It does not sell accounts and does not provide guarantees.
Never store passwords or login credentials.
"""

import json
import sqlite3
import uuid

from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone

from .settings import DATABASE_PATH


def current_time():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_encode(value):
    return json.dumps(value or {}, ensure_ascii=False)


def json_decode(value, default=None):
    if default is None:
        default = {}

    if not value:
        return default

    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


class Database:
    """Main SQLite database manager."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DATABASE_PATH)

        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(
                parents=True,
                exist_ok=True
            )

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(
            self.db_path,
            timeout=30
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row):
        return dict(row) if row is not None else None

    def initialize(self):
        """Create database tables and indexes."""

        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS guarantors (
                    user_id INTEGER PRIMARY KEY,
                    display_name TEXT,
                    subscription_status TEXT NOT NULL DEFAULT 'inactive',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    added_by INTEGER,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lot_code TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price REAL NOT NULL CHECK(price >= 0),
                    currency TEXT NOT NULL DEFAULT 'TJS',
                    category TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    video_url TEXT NOT NULL DEFAULT '',
                    guarantor_user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'available',
                    account_level TEXT,
                    classic_level TEXT,
                    metro_level TEXT,
                    collection_level TEXT,
                    upgrades_count INTEGER DEFAULT 0,
                    mythic_count INTEGER DEFAULT 0,
                    account_age TEXT,
                    bindings_json TEXT NOT NULL DEFAULT '{}',
                    full_binding_available INTEGER NOT NULL DEFAULT 0,
                    important_info TEXT,
                    extra_info TEXT,
                    source_channel_id TEXT,
                    source_message_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(guarantor_user_id)
                        REFERENCES guarantors(user_id)
                );

                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_name TEXT NOT NULL,
                    plan_version TEXT NOT NULL DEFAULT '1.0',
                    status TEXT NOT NULL DEFAULT 'waiting',
                    timer_mode TEXT NOT NULL DEFAULT 'normal',
                    starts_at TEXT,
                    expires_at TEXT,
                    remaining_seconds INTEGER NOT NULL DEFAULT 0,
                    is_started INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payer_user_id INTEGER NOT NULL,
                    amount REAL NOT NULL CHECK(amount >= 0),
                    currency TEXT NOT NULL DEFAULT 'TJS',
                    purpose TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    payment_reference TEXT,
                    confirmed_by INTEGER,
                    created_at TEXT NOT NULL,
                    confirmed_at TEXT,
                    FOREIGN KEY(payer_user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS commissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guarantor_user_id INTEGER NOT NULL,
                    lot_code TEXT,
                    amount REAL NOT NULL CHECK(amount >= 0),
                    currency TEXT NOT NULL DEFAULT 'TJS',
                    status TEXT NOT NULL DEFAULT 'unpaid',
                    note TEXT,
                    created_at TEXT NOT NULL,
                    paid_at TEXT,
                    paid_by INTEGER,
                    FOREIGN KEY(guarantor_user_id)
                        REFERENCES guarantors(user_id)
                );

                CREATE TABLE IF NOT EXISTS bonuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    bonus_type TEXT NOT NULL,
                    bonus_value TEXT,
                    source TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS ai_credit_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    source TEXT,
                    reference_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS rules_acceptances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    rules_version TEXT NOT NULL,
                    accepted INTEGER NOT NULL DEFAULT 1,
                    accepted_at TEXT NOT NULL,
                    UNIQUE(user_id, rules_version),
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_user_id INTEGER,
                    action TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id TEXT,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_lots_status
                    ON lots(status);

                CREATE INDEX IF NOT EXISTS idx_lots_category
                    ON lots(category);

                CREATE INDEX IF NOT EXISTS idx_lots_guarantor
                    ON lots(guarantor_user_id);

                CREATE INDEX IF NOT EXISTS idx_subscriptions_user
                    ON subscriptions(user_id);

                CREATE INDEX IF NOT EXISTS idx_subscriptions_status
                    ON subscriptions(status);

                CREATE INDEX IF NOT EXISTS idx_payments_status
                    ON payments(status);

                CREATE INDEX IF NOT EXISTS idx_logs_created
                    ON audit_logs(created_at);
            """)

        return True

    # --------------------------------------------------
    # USERS
    # --------------------------------------------------

    def add_user(
        self,
        user_id,
        username=None,
        full_name=None,
        role="user"
    ):
        now = current_time()

        with self.connection() as conn:
            conn.execute("""
                INSERT INTO users (
                    user_id, username, full_name, role,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name,
                    updated_at = excluded.updated_at
            """, (
                user_id, username, full_name,
                role, now, now
            ))

        return user_id

    def get_user(self, user_id):
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()

        return self._row_to_dict(row)

    def set_user_active(self, user_id, is_active):
        with self.connection() as conn:
            cursor = conn.execute("""
                UPDATE users
                SET is_active = ?, updated_at = ?
                WHERE user_id = ?
            """, (int(bool(is_active)), current_time(), user_id))

        return cursor.rowcount > 0

    # --------------------------------------------------
    # GUARANTORS
    # --------------------------------------------------

    def add_guarantor(
        self,
        user_id,
        display_name=None,
        username=None,
        full_name=None
    ):
        self.add_user(
            user_id,
            username=username,
            full_name=full_name,
            role="guarantor"
        )

        with self.connection() as conn:
            conn.execute("""
                INSERT INTO guarantors (
                    user_id, display_name, created_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    display_name = excluded.display_name
            """, (user_id, display_name, current_time()))

        return user_id

    def get_guarantor(self, user_id):
        with self.connection() as conn:
            row = conn.execute("""
                SELECT g.*, u.username, u.full_name, u.is_active
                FROM guarantors g
                JOIN users u ON u.user_id = g.user_id
                WHERE g.user_id = ?
            """, (user_id,)).fetchone()

        return self._row_to_dict(row)

    # --------------------------------------------------
    # CHANNELS
    # --------------------------------------------------

    def add_channel(
        self,
        channel_id,
        title,
        purpose,
        added_by=None
    ):
        now = current_time()

        with self.connection() as conn:
            conn.execute("""
                INSERT INTO channels (
                    channel_id, title, purpose, added_by,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    title = excluded.title,
                    purpose = excluded.purpose,
                    added_by = excluded.added_by,
                    updated_at = excluded.updated_at
            """, (
                str(channel_id), title, purpose,
                added_by, now, now
            ))

        return str(channel_id)

    def get_channels(self, active_only=True):
        query = "SELECT * FROM channels"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY created_at DESC"

        with self.connection() as conn:
            rows = conn.execute(query).fetchall()

        return [dict(row) for row in rows]

    def set_channel_active(self, channel_id, is_active):
        with self.connection() as conn:
            cursor = conn.execute("""
                UPDATE channels
                SET is_active = ?, updated_at = ?
                WHERE channel_id = ?
            """, (
                int(bool(is_active)),
                current_time(),
                str(channel_id)
            ))

        return cursor.rowcount > 0

    # --------------------------------------------------
    # LOTS
    # --------------------------------------------------

    def add_lot(self, data):
        required = (
            "title",
            "description",
            "price",
            "category",
            "platform",
            "guarantor_user_id"
        )

        for key in required:
            if key not in data:
                raise ValueError(f"Missing lot field: {key}")

        price = float(data["price"])
        if price < 0:
            raise ValueError("Price cannot be negative")

        lot_code = data.get("lot_code")
        if not lot_code:
            lot_code = "MX-" + uuid.uuid4().hex[:10].upper()

        now = current_time()

        with self.connection() as conn:
            conn.execute("""
                INSERT INTO lots (
                    lot_code, title, description, price, currency,
                    category, platform, video_url,
                    guarantor_user_id, status,
                    account_level, classic_level, metro_level,
                    collection_level, upgrades_count, mythic_count,
                    account_age, bindings_json,
                    full_binding_available, important_info,
                    extra_info, source_channel_id,
                    source_message_id, created_at, updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                lot_code,
                data["title"],
                data["description"],
                price,
                data.get("currency", "TJS"),
                data["category"],
                data["platform"],
                data.get("video_url", ""),
                data["guarantor_user_id"],
                data.get("status", "available"),
                data.get("account_level"),
                data.get("classic_level"),
                data.get("metro_level"),
                data.get("collection_level"),
                data.get("upgrades_count", 0),
                data.get("mythic_count", 0),
                data.get("account_age"),
                json_encode(data.get("bindings", {})),
                int(bool(data.get("full_binding_available", False))),
                data.get("important_info"),
                data.get("extra_info"),
                data.get("source_channel_id"),
                data.get("source_message_id"),
                now,
                now
            ))

        return lot_code

    def get_lot(self, lot_code):
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM lots WHERE lot_code = ?",
                (lot_code,)
            ).fetchone()

        item = self._row_to_dict(row)
        if item:
            item["bindings"] = json_decode(
                item.pop("bindings_json", "{}")
            )

        return item

    def list_lots(
        self,
        status=None,
        category=None,
        limit=50,
        offset=0
    ):
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))

        query = "SELECT * FROM lots WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.connection() as conn:
            rows = conn.execute(query, params).fetchall()

        results = []
        for row in rows:
            item = dict(row)
            item["bindings"] = json_decode(
                item.pop("bindings_json", "{}")
            )
            results.append(item)

        return results

    def update_lot(self, lot_code, data):
        allowed = {
            "title", "description", "price", "currency",
            "category", "platform", "video_url", "status",
            "account_level", "classic_level", "metro_level",
            "collection_level", "upgrades_count", "mythic_count",
            "account_age", "full_binding_available",
            "important_info", "extra_info"
        }

        updates = []
        values = []

        for key, value in data.items():
            if key not in allowed:
                continue

            if key == "full_binding_available":
                value = int(bool(value))

            updates.append(f"{key} = ?")
            values.append(value)

        if "bindings" in data:
            updates.append("bindings_json = ?")
            values.append(json_encode(data["bindings"]))

        if not updates:
            return False

        updates.append("updated_at = ?")
        values.append(current_time())
        values.append(lot_code)

        with self.connection() as conn:
            cursor = conn.execute(
                f"UPDATE lots SET {', '.join(updates)} WHERE lot_code = ?",
                values
            )

        return cursor.rowcount > 0

    def set_lot_status(self, lot_code, status):
        allowed = {"available", "reserved", "sold", "inactive"}
        if status not in allowed:
            raise ValueError("Invalid lot status")

        return self.update_lot(lot_code, {"status": status})

    # --------------------------------------------------
    # SUBSCRIPTIONS
    # --------------------------------------------------

    def create_subscription(
        self,
        user_id,
        plan_name,
        plan_version="1.0",
        status="waiting",
        timer_mode="normal",
        remaining_seconds=0,
        starts_at=None,
        expires_at=None,
        is_started=False,
        **kwargs
    ):
        if kwargs.get("is_vip_pluss"):
            timer_mode = "vip_pluss"

        if kwargs.get("started_at") and not starts_at:
            starts_at = kwargs["started_at"]

        now = current_time()

        
                with self.connection() as conn:
cursor = conn.execute("""
INSERT INTO subscriptions (
user_id, plan_name, plan_version,
status, timer_mode, starts_at, expires_at,
remaining_seconds, is_started,
created_at, updated_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
user_id,
                plan_name,
                plan_version,
                status,
                timer_mode,
                starts_at,
                expires_at,
                int(remaining_seconds or 0),
                int(bool(is_started)),
                now,
                now
            ))

            return cursor.lastrowid
