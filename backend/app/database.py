import secrets
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

from backend.app.security import hash_access_token

AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL COLLATE NOCASE UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at ON auth_sessions(expires_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_house_members_unique_name
ON house_members(house_id, user_name);
CREATE INDEX IF NOT EXISTS idx_house_members_user_name ON house_members(user_name);
"""

LEGACY_SCHEMA = """
CREATE TABLE IF NOT EXISTS houses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    invite_code TEXT NOT NULL UNIQUE,
    created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS house_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id INTEGER NOT NULL,
    user_name TEXT NOT NULL,
    role TEXT NOT NULL,
    FOREIGN KEY (house_id) REFERENCES houses(id)
);
CREATE TABLE IF NOT EXISTS chores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    assigned_to TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shopping_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    added_by TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    debtor TEXT NOT NULL,
    creditor TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL
);
"""


class DuplicateUserError(Exception):
    def __init__(self, field: str):
        self.field = field
        super().__init__(field)


class Database:
    def __init__(self, path: Path):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.session() as connection:
            connection.executescript(LEGACY_SCHEMA)
            connection.executescript(AUTH_SCHEMA)
            member_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(house_members)")
            }
            if "user_id" not in member_columns:
                connection.execute(
                    "ALTER TABLE house_members ADD COLUMN user_id INTEGER REFERENCES users(id)"
                )
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_house_members_unique_user
                ON house_members(house_id, user_id)
                WHERE user_id IS NOT NULL
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (1, self._now()),
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (2, self._now()),
            )

    def create_user(self, email: str, password_hash: str, display_name: str) -> dict[str, Any]:
        with self.session() as connection:
            existing_email = connection.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing_email:
                raise DuplicateUserError("email")

            existing_name = connection.execute(
                "SELECT id FROM users WHERE display_name = ?", (display_name,)
            ).fetchone()
            if existing_name:
                raise DuplicateUserError("display_name")

            cursor = connection.execute(
                """
                INSERT INTO users (email, password_hash, display_name, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (email, password_hash, display_name, self._now()),
            )
            user_id = int(cursor.lastrowid)
            row = connection.execute(
                "SELECT id, email, display_name FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return dict(row)

    def get_user_with_password(self, email: str) -> dict[str, Any] | None:
        with self.session() as connection:
            row = connection.execute(
                "SELECT id, email, display_name, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        return dict(row) if row else None

    def create_session(self, user_id: int, token: str, days: int = 30) -> None:
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=days)
        with self.session() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE expires_at <= ?", (now.isoformat(),)
            )
            connection.execute(
                """
                INSERT INTO auth_sessions (user_id, token_hash, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, hash_access_token(token), now.isoformat(), expires_at.isoformat()),
            )

    def get_user_by_token(self, token: str) -> dict[str, Any] | None:
        with self.session() as connection:
            row = connection.execute(
                """
                SELECT u.id, u.email, u.display_name
                FROM auth_sessions session
                JOIN users u ON u.id = session.user_id
                WHERE session.token_hash = ? AND session.expires_at > ?
                """,
                (hash_access_token(token), self._now()),
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, token: str) -> None:
        with self.session() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE token_hash = ?", (hash_access_token(token),)
            )

    def list_houses(self, user_id: int) -> list[dict[str, Any]]:
        with self.session() as connection:
            rows = connection.execute(
                """
                SELECT h.id, h.name, h.location, h.invite_code, h.created_by,
                       COUNT(all_members.id) AS member_count
                FROM houses h
                JOIN house_members own_membership ON own_membership.house_id = h.id
                LEFT JOIN house_members all_members ON all_members.house_id = h.id
                WHERE own_membership.user_id = ?
                GROUP BY h.id
                ORDER BY h.id DESC
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_house(
        self, name: str, location: str, user_id: int, display_name: str
    ) -> dict[str, Any]:
        with self.session() as connection:
            for _ in range(5):
                invite_code = f"RS-{secrets.token_hex(3).upper()}"
                try:
                    cursor = connection.execute(
                        """
                        INSERT INTO houses (name, location, invite_code, created_by)
                        VALUES (?, ?, ?, ?)
                        """,
                        (name, location, invite_code, display_name),
                    )
                    house_id = int(cursor.lastrowid)
                    connection.execute(
                        """
                        INSERT INTO house_members (house_id, user_name, role, user_id)
                        VALUES (?, ?, 'owner', ?)
                        """,
                        (house_id, display_name, user_id),
                    )
                    row = connection.execute(
                        """
                        SELECT id, name, location, invite_code, created_by, 1 AS member_count
                        FROM houses WHERE id = ?
                        """,
                        (house_id,),
                    ).fetchone()
                    return dict(row)
                except sqlite3.IntegrityError as error:
                    if "invite_code" not in str(error):
                        raise

        raise RuntimeError("고유한 초대코드를 생성하지 못했습니다.")

    def is_house_member(self, house_id: int, user_id: int) -> bool:
        with self.session() as connection:
            row = connection.execute(
                "SELECT 1 FROM house_members WHERE house_id = ? AND user_id = ?",
                (house_id, user_id),
            ).fetchone()
        return row is not None

    def list_validated_chores(self, house_id: int) -> list[dict[str, Any]]:
        """Return only chores assigned to a member of the same house."""
        with self.session() as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.title, c.due_date, c.status,
                       member.user_id AS assignee_user_id,
                       COALESCE(user.display_name, member.user_name) AS assignee_display_name
                FROM chores c
                JOIN house_members member
                  ON member.house_id = c.house_id
                 AND member.user_name = c.assigned_to
                LEFT JOIN users user ON user.id = member.user_id
                WHERE c.house_id = ?
                ORDER BY c.due_date ASC, c.id ASC
                """,
                (house_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_chore_status(
        self, house_id: int, chore_id: int, chore_status: str
    ) -> dict[str, Any] | None:
        with self.session() as connection:
            cursor = connection.execute(
                """
                UPDATE chores
                SET status = ?
                WHERE id = ? AND house_id = ?
                  AND EXISTS (
                    SELECT 1 FROM house_members member
                    WHERE member.house_id = chores.house_id
                      AND member.user_name = chores.assigned_to
                  )
                """,
                (chore_status, chore_id, house_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                """
                SELECT c.id, c.title, c.due_date, c.status,
                       member.user_id AS assignee_user_id,
                       COALESCE(user.display_name, member.user_name) AS assignee_display_name
                FROM chores c
                JOIN house_members member
                  ON member.house_id = c.house_id
                 AND member.user_name = c.assigned_to
                LEFT JOIN users user ON user.id = member.user_id
                WHERE c.id = ? AND c.house_id = ?
                """,
                (chore_id, house_id),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
