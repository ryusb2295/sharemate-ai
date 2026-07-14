import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app


class HouseJoinApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "test.db"
        await self.start_app()

    async def start_app(self) -> None:
        self.app = create_app(self.database_path)
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://test"
        )

    async def stop_app(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    async def asyncTearDown(self) -> None:
        await self.stop_app()
        self.temp_directory.cleanup()

    async def signup(self, email: str, display_name: str) -> dict[str, object]:
        response = await self.client.post(
            "/auth/signup",
            json={
                "email": email,
                "password": "correct-password",
                "display_name": display_name,
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    @staticmethod
    def headers(auth: dict[str, object]) -> dict[str, str]:
        return {"Authorization": f"Bearer {auth['access_token']}"}

    async def test_user_a_b_join_flow_duplicate_invalid_and_restart(self) -> None:
        user_a = await self.signup("owner@example.com", "사용자A")
        create = await self.client.post(
            "/houses",
            headers=self.headers(user_a),
            json={"name": "House A", "location": "Sydney"},
        )
        self.assertEqual(create.status_code, 201)
        house = create.json()
        invite_code = house["invite_code"]
        self.assertRegex(invite_code, r"^[A-Z0-9]{8}$")
        self.assertEqual(house["owner_id"], user_a["user"]["id"])
        self.assertEqual(house["member_count"], 1)

        user_b = await self.signup("member@example.com", "사용자B")
        join = await self.client.post(
            "/houses/join",
            headers=self.headers(user_b),
            json={"invite_code": invite_code.lower()},
        )
        self.assertEqual(join.status_code, 200)
        self.assertEqual(join.json()["id"], house["id"])
        self.assertEqual(join.json()["member_count"], 2)

        members = await self.client.get(
            f"/houses/{house['id']}/members", headers=self.headers(user_b)
        )
        self.assertEqual(members.status_code, 200)
        self.assertEqual(
            [(item["display_name"], item["role"]) for item in members.json()],
            [("사용자A", "owner"), ("사용자B", "member")],
        )

        duplicate = await self.client.post(
            "/houses/join",
            headers=self.headers(user_b),
            json={"invite_code": invite_code},
        )
        self.assertEqual(duplicate.status_code, 409)
        members_after_duplicate = await self.client.get(
            f"/houses/{house['id']}/members", headers=self.headers(user_b)
        )
        self.assertEqual(len(members_after_duplicate.json()), 2)

        invalid = await self.client.post(
            "/houses/join",
            headers=self.headers(user_b),
            json={"invite_code": "ZZZZZZZZ"},
        )
        empty = await self.client.post(
            "/houses/join",
            headers=self.headers(user_b),
            json={"invite_code": "   "},
        )
        self.assertEqual(invalid.status_code, 404)
        self.assertEqual(empty.status_code, 400)

        detail = await self.client.get(
            f"/houses/{house['id']}", headers=self.headers(user_b)
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["invite_code"], invite_code)

        await self.stop_app()
        await self.start_app()
        login_b = await self.client.post(
            "/auth/login",
            json={"email": "member@example.com", "password": "correct-password"},
        )
        houses = await self.client.get(
            "/houses", headers=self.headers(login_b.json())
        )
        self.assertEqual(houses.status_code, 200)
        self.assertEqual([item["id"] for item in houses.json()], [house["id"]])

    async def test_non_member_cannot_read_house_or_members(self) -> None:
        owner = await self.signup("owner2@example.com", "소유자")
        house = (
            await self.client.post(
                "/houses",
                headers=self.headers(owner),
                json={"name": "Private House", "location": "Sydney"},
            )
        ).json()
        outsider = await self.signup("outside@example.com", "외부인")
        detail = await self.client.get(
            f"/houses/{house['id']}", headers=self.headers(outsider)
        )
        members = await self.client.get(
            f"/houses/{house['id']}/members", headers=self.headers(outsider)
        )
        self.assertEqual(detail.status_code, 403)
        self.assertEqual(members.status_code, 403)

    async def test_house_join_and_member_endpoints_require_authentication(self) -> None:
        join = await self.client.post(
            "/houses/join", json={"invite_code": "AB12CD34"}
        )
        detail = await self.client.get("/houses/1")
        members = await self.client.get("/houses/1/members")
        self.assertEqual(join.status_code, 401)
        self.assertEqual(detail.status_code, 401)
        self.assertEqual(members.status_code, 401)

    async def test_schema_has_safe_membership_columns_and_constraints(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            house_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(houses)")
            }
            member_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(house_members)")
            }
            member_indexes = {
                row[1]: row[2]
                for row in connection.execute("PRAGMA index_list(house_members)")
            }
            chore_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(chores)")
            }
        self.assertTrue({"owner_id", "created_at"}.issubset(house_columns))
        self.assertIn("joined_at", member_columns)
        self.assertEqual(member_indexes["idx_house_members_unique_user"], 1)
        self.assertTrue(
            {
                "description",
                "assignee_user_id",
                "scheduled_date",
                "completed_at",
                "created_by",
                "created_at",
            }.issubset(chore_columns)
        )


class LegacyHouseMigrationTest(unittest.TestCase):
    def test_legacy_house_is_preserved_and_invite_code_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "legacy.db"
            with closing(sqlite3.connect(database_path)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE houses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        location TEXT NOT NULL,
                        invite_code TEXT NOT NULL UNIQUE,
                        created_by TEXT NOT NULL
                    );
                    CREATE TABLE house_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        house_id INTEGER NOT NULL,
                        user_name TEXT NOT NULL,
                        role TEXT NOT NULL
                    );
                    INSERT INTO houses (name, location, invite_code, created_by)
                    VALUES ('Legacy House', 'Sydney', 'RS-ABC123', 'legacy-owner');
                    INSERT INTO house_members (house_id, user_name, role)
                    VALUES (1, 'legacy-owner', 'owner');
                    """
                )

            database = create_app(database_path)

            async def migrate() -> None:
                lifespan = database.router.lifespan_context(database)
                await lifespan.__aenter__()
                await lifespan.__aexit__(None, None, None)

            import asyncio

            asyncio.run(migrate())
            with closing(sqlite3.connect(database_path)) as connection:
                row = connection.execute(
                    "SELECT name, location, invite_code, created_at FROM houses WHERE id = 1"
                ).fetchone()
            self.assertEqual(row[0:2], ("Legacy House", "Sydney"))
            self.assertRegex(row[2], re.compile(r"^[A-Z0-9]{8}$"))
            self.assertTrue(row[3])
            self.assertEqual(
                len(list((database_path.parent / "backups").glob("*.db"))), 1
            )


if __name__ == "__main__":
    unittest.main()
