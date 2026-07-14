import secrets
import sqlite3
import re
from contextlib import closing, contextmanager
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


class HouseNotFoundError(Exception):
    pass


class AlreadyHouseMemberError(Exception):
    pass


class Database:
    INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

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
        self._backup_before_house_invite_migration()
        self._backup_before_chore_migration()
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
            house_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(houses)")
            }
            if "owner_id" not in house_columns:
                connection.execute(
                    "ALTER TABLE houses ADD COLUMN owner_id INTEGER REFERENCES users(id)"
                )
            if "created_at" not in house_columns:
                connection.execute("ALTER TABLE houses ADD COLUMN created_at TEXT")
            if "joined_at" not in member_columns:
                connection.execute("ALTER TABLE house_members ADD COLUMN joined_at TEXT")

            connection.execute(
                """
                UPDATE house_members
                SET user_id = (
                    SELECT users.id FROM users
                    WHERE users.display_name = house_members.user_name
                )
                WHERE user_id IS NULL
                  AND EXISTS (
                    SELECT 1 FROM users
                    WHERE users.display_name = house_members.user_name
                  )
                """
            )
            connection.execute(
                """
                UPDATE houses
                SET owner_id = (
                    SELECT member.user_id
                    FROM house_members member
                    WHERE member.house_id = houses.id
                      AND member.role = 'owner'
                      AND member.user_id IS NOT NULL
                    ORDER BY member.id ASC
                    LIMIT 1
                )
                WHERE owner_id IS NULL
                """
            )
            now = self._now()
            connection.execute(
                "UPDATE houses SET created_at = ? WHERE created_at IS NULL OR created_at = ''",
                (now,),
            )
            connection.execute(
                "UPDATE house_members SET joined_at = ? WHERE joined_at IS NULL OR joined_at = ''",
                (now,),
            )

            used_codes: set[str] = set()
            invalid_houses = connection.execute(
                "SELECT id, invite_code FROM houses ORDER BY id"
            ).fetchall()
            for house in invalid_houses:
                current_code = str(house["invite_code"]).upper()
                if re.fullmatch(r"[A-Z0-9]{6,8}", current_code) and current_code not in used_codes:
                    if current_code != house["invite_code"]:
                        connection.execute(
                            "UPDATE houses SET invite_code = ? WHERE id = ?",
                            (current_code, int(house["id"])),
                        )
                    used_codes.add(current_code)
                    continue
                replacement = self._new_invite_code(used_codes)
                connection.execute(
                    "UPDATE houses SET invite_code = ? WHERE id = ?",
                    (replacement, int(house["id"])),
                )
                used_codes.add(replacement)
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
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (3, self._now()),
            )

            chore_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(chores)")
            }
            chore_column_definitions = {
                "description": "TEXT",
                "assignee_user_id": "INTEGER REFERENCES users(id)",
                "scheduled_date": "TEXT",
                "completed_at": "TEXT",
                "created_by": "INTEGER REFERENCES users(id)",
                "created_at": "TEXT",
            }
            for column, definition in chore_column_definitions.items():
                if column not in chore_columns:
                    connection.execute(
                        f"ALTER TABLE chores ADD COLUMN {column} {definition}"
                    )
            connection.execute(
                "UPDATE chores SET description = '' WHERE description IS NULL"
            )
            connection.execute(
                """
                UPDATE chores
                SET assignee_user_id = (
                    SELECT member.user_id
                    FROM house_members member
                    WHERE member.house_id = chores.house_id
                      AND member.user_name = chores.assigned_to
                      AND member.user_id IS NOT NULL
                    LIMIT 1
                )
                WHERE assignee_user_id IS NULL
                """
            )
            connection.execute(
                """
                UPDATE chores
                SET scheduled_date = due_date
                WHERE scheduled_date IS NULL OR scheduled_date = ''
                """
            )
            connection.execute(
                """
                UPDATE chores
                SET created_by = COALESCE(
                    (SELECT houses.owner_id FROM houses WHERE houses.id = chores.house_id),
                    assignee_user_id
                )
                WHERE created_by IS NULL
                """
            )
            connection.execute(
                "UPDATE chores SET created_at = ? WHERE created_at IS NULL OR created_at = ''",
                (now,),
            )
            connection.execute(
                """
                UPDATE chores
                SET completed_at = ?
                WHERE status = '완료' AND completed_at IS NULL
                """,
                (now,),
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_chores_house_date ON chores(house_id, scheduled_date)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_chores_assignee ON chores(house_id, assignee_user_id)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (4, self._now()),
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
                       h.owner_id, h.created_at,
                       COUNT(all_members.id) AS member_count
                FROM houses h
                JOIN house_members own_membership ON own_membership.house_id = h.id
                LEFT JOIN house_members all_members
                  ON all_members.house_id = h.id AND all_members.user_id IS NOT NULL
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
            for _ in range(10):
                invite_code = self._new_invite_code()
                try:
                    cursor = connection.execute(
                        """
                        INSERT INTO houses
                            (name, location, invite_code, created_by, owner_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (name, location, invite_code, display_name, user_id, self._now()),
                    )
                    house_id = int(cursor.lastrowid)
                    connection.execute(
                        """
                        INSERT INTO house_members
                            (house_id, user_name, role, user_id, joined_at)
                        VALUES (?, ?, 'owner', ?, ?)
                        """,
                        (house_id, display_name, user_id, self._now()),
                    )
                    row = connection.execute(
                        """
                        SELECT id, name, location, invite_code, created_by,
                               owner_id, created_at, 1 AS member_count
                        FROM houses WHERE id = ?
                        """,
                        (house_id,),
                    ).fetchone()
                    return dict(row)
                except sqlite3.IntegrityError as error:
                    if "invite_code" not in str(error):
                        raise

        raise RuntimeError("고유한 초대코드를 생성하지 못했습니다.")

    def get_house(self, house_id: int, user_id: int) -> dict[str, Any] | None:
        with self.session() as connection:
            row = connection.execute(
                """
                SELECT h.id, h.name, h.location, h.invite_code, h.created_by,
                       h.owner_id, h.created_at,
                       COUNT(member.id) AS member_count
                FROM houses h
                JOIN house_members own_membership
                  ON own_membership.house_id = h.id AND own_membership.user_id = ?
                LEFT JOIN house_members member
                  ON member.house_id = h.id AND member.user_id IS NOT NULL
                WHERE h.id = ?
                GROUP BY h.id
                """,
                (user_id, house_id),
            ).fetchone()
        return dict(row) if row else None

    def join_house_by_invite(
        self, invite_code: str, user_id: int, display_name: str
    ) -> dict[str, Any]:
        with self.session() as connection:
            house = connection.execute(
                "SELECT id FROM houses WHERE invite_code = ?",
                (invite_code,),
            ).fetchone()
            if house is None:
                raise HouseNotFoundError(invite_code)
            house_id = int(house["id"])
            existing = connection.execute(
                "SELECT id FROM house_members WHERE house_id = ? AND user_id = ?",
                (house_id, user_id),
            ).fetchone()
            if existing:
                raise AlreadyHouseMemberError(invite_code)
            try:
                connection.execute(
                    """
                    INSERT INTO house_members
                        (house_id, user_name, role, user_id, joined_at)
                    VALUES (?, ?, 'member', ?, ?)
                    """,
                    (house_id, display_name, user_id, self._now()),
                )
            except sqlite3.IntegrityError as error:
                raise AlreadyHouseMemberError(invite_code) from error
            row = connection.execute(
                """
                SELECT h.id, h.name, h.location, h.invite_code, h.created_by,
                       h.owner_id, h.created_at,
                       COUNT(member.id) AS member_count
                FROM houses h
                LEFT JOIN house_members member
                  ON member.house_id = h.id AND member.user_id IS NOT NULL
                WHERE h.id = ?
                GROUP BY h.id
                """,
                (house_id,),
            ).fetchone()
        return dict(row)

    def list_house_members(self, house_id: int) -> list[dict[str, Any]]:
        with self.session() as connection:
            rows = connection.execute(
                """
                SELECT member.id, member.house_id, member.user_id,
                       user.display_name, user.email, member.role, member.joined_at
                FROM house_members member
                JOIN users user ON user.id = member.user_id
                WHERE member.house_id = ?
                ORDER BY CASE member.role WHEN 'owner' THEN 0 ELSE 1 END,
                         member.joined_at ASC, member.id ASC
                """,
                (house_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def is_house_member(self, house_id: int, user_id: int) -> bool:
        with self.session() as connection:
            row = connection.execute(
                "SELECT 1 FROM house_members WHERE house_id = ? AND user_id = ?",
                (house_id, user_id),
            ).fetchone()
        return row is not None

    def list_validated_chores(self, house_id: int) -> list[dict[str, Any]]:
        """Return only chores assigned to a registered member of the same house."""
        with self.session() as connection:
            rows = connection.execute(
                f"""
                {self._chore_select_sql()}
                WHERE chore.house_id = ?
                ORDER BY chore.scheduled_date ASC, chore.id ASC
                """,
                (house_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_chore(
        self,
        house_id: int,
        title: str,
        description: str,
        assignee_user_id: int,
        scheduled_date: str,
        created_by: int,
    ) -> dict[str, Any] | None:
        with self.session() as connection:
            assignee = connection.execute(
                """
                SELECT user.display_name
                FROM house_members member
                JOIN users user ON user.id = member.user_id
                WHERE member.house_id = ? AND member.user_id = ?
                """,
                (house_id, assignee_user_id),
            ).fetchone()
            if assignee is None:
                return None
            cursor = connection.execute(
                """
                INSERT INTO chores (
                    house_id, title, assigned_to, due_date, status,
                    description, assignee_user_id, scheduled_date,
                    completed_at, created_by, created_at
                ) VALUES (?, ?, ?, ?, '진행 전', ?, ?, ?, NULL, ?, ?)
                """,
                (
                    house_id,
                    title,
                    str(assignee["display_name"]),
                    scheduled_date,
                    description,
                    assignee_user_id,
                    scheduled_date,
                    created_by,
                    self._now(),
                ),
            )
            row = self._get_chore_row(connection, house_id, int(cursor.lastrowid))
        return dict(row) if row else None

    def update_chore(
        self,
        house_id: int,
        chore_id: int,
        changes: dict[str, Any],
    ) -> dict[str, Any] | None:
        with self.session() as connection:
            if self._get_chore_row(connection, house_id, chore_id) is None:
                return None
            assignments: list[str] = []
            values: list[Any] = []
            if "title" in changes:
                assignments.append("title = ?")
                values.append(changes["title"])
            if "description" in changes:
                assignments.append("description = ?")
                values.append(changes["description"])
            if "scheduled_date" in changes:
                assignments.extend(["scheduled_date = ?", "due_date = ?"])
                values.extend([changes["scheduled_date"], changes["scheduled_date"]])
            if "assignee_user_id" in changes:
                assignee = connection.execute(
                    """
                    SELECT user.display_name
                    FROM house_members member
                    JOIN users user ON user.id = member.user_id
                    WHERE member.house_id = ? AND member.user_id = ?
                    """,
                    (house_id, changes["assignee_user_id"]),
                ).fetchone()
                if assignee is None:
                    return None
                assignments.extend(["assignee_user_id = ?", "assigned_to = ?"])
                values.extend(
                    [changes["assignee_user_id"], str(assignee["display_name"])]
                )
            if assignments:
                values.extend([chore_id, house_id])
                connection.execute(
                    f"UPDATE chores SET {', '.join(assignments)} WHERE id = ? AND house_id = ?",
                    values,
                )
            row = self._get_chore_row(connection, house_id, chore_id)
        return dict(row) if row else None

    def set_chore_completion(
        self, house_id: int, chore_id: int, is_completed: bool
    ) -> dict[str, Any] | None:
        with self.session() as connection:
            cursor = connection.execute(
                """
                UPDATE chores
                SET status = ?, completed_at = ?
                WHERE id = ? AND house_id = ?
                """,
                (
                    "완료" if is_completed else "진행 전",
                    self._now() if is_completed else None,
                    chore_id,
                    house_id,
                ),
            )
            if cursor.rowcount == 0:
                return None
            row = self._get_chore_row(connection, house_id, chore_id)
        return dict(row) if row else None

    def delete_chore(self, house_id: int, chore_id: int) -> bool:
        with self.session() as connection:
            cursor = connection.execute(
                "DELETE FROM chores WHERE id = ? AND house_id = ?",
                (chore_id, house_id),
            )
        return cursor.rowcount > 0

    @staticmethod
    def _chore_select_sql() -> str:
        return """
            SELECT chore.id, chore.house_id, chore.title,
                   COALESCE(chore.description, '') AS description,
                   chore.assignee_user_id, chore.scheduled_date,
                   chore.status, chore.completed_at,
                   chore.created_by, chore.created_at,
                   user.display_name AS assignee_display_name
            FROM chores chore
            JOIN house_members member
              ON member.house_id = chore.house_id
             AND member.user_id = chore.assignee_user_id
            JOIN users user ON user.id = member.user_id
        """

    def _get_chore_row(
        self, connection: sqlite3.Connection, house_id: int, chore_id: int
    ) -> sqlite3.Row | None:
        return connection.execute(
            f"""
            {self._chore_select_sql()}
            WHERE chore.house_id = ? AND chore.id = ?
            """,
            (house_id, chore_id),
        ).fetchone()

    def _backup_before_house_invite_migration(self) -> Path | None:
        if not self.path.exists():
            return None
        with closing(sqlite3.connect(self.path)) as connection:
            has_houses = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'houses'"
            ).fetchone()
            has_migrations = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
            ).fetchone()
            already_migrated = (
                connection.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = 3"
                ).fetchone()
                if has_migrations
                else None
            )
        if not has_houses or already_migrated:
            return None

        backup_directory = self.path.parent / "backups"
        backup_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = backup_directory / f"{self.path.stem}-before-house-invites-{timestamp}.db"
        with closing(sqlite3.connect(self.path)) as source:
            with closing(sqlite3.connect(backup_path)) as destination:
                source.backup(destination)
        return backup_path

    def _backup_before_chore_migration(self) -> Path | None:
        if not self.path.exists():
            return None
        with closing(sqlite3.connect(self.path)) as connection:
            has_chores = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'chores'"
            ).fetchone()
            has_migrations = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
            ).fetchone()
            already_migrated = (
                connection.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = 4"
                ).fetchone()
                if has_migrations
                else None
            )
        if not has_chores or already_migrated:
            return None

        backup_directory = self.path.parent / "backups"
        backup_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = backup_directory / f"{self.path.stem}-before-chores-{timestamp}.db"
        with closing(sqlite3.connect(self.path)) as source:
            with closing(sqlite3.connect(backup_path)) as destination:
                source.backup(destination)
        return backup_path

    def _new_invite_code(self, existing: set[str] | None = None) -> str:
        occupied = existing or set()
        for _ in range(100):
            code = "".join(secrets.choice(self.INVITE_CODE_ALPHABET) for _ in range(8))
            if code not in occupied:
                return code
        raise RuntimeError("고유한 초대코드를 생성하지 못했습니다.")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
