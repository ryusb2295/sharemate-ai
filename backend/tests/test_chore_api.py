import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app


class ChoreApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp_directory.name) / "test.db")
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = AsyncClient(transport=ASGITransport(app=self.app), base_url="http://test")

        signup = await self.client.post(
            "/auth/signup",
            json={
                "email": "solo@example.com",
                "password": "correct-password",
                "display_name": "혼자사용자",
            },
        )
        self.assertEqual(signup.status_code, 201)
        self.auth = signup.json()
        self.headers = {"Authorization": f"Bearer {self.auth['access_token']}"}
        house = await self.client.post(
            "/houses",
            headers=self.headers,
            json={"name": "Solo House", "location": "Sydney"},
        )
        self.assertEqual(house.status_code, 201)
        self.house_id = house.json()["id"]

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)
        self.temp_directory.cleanup()

    def insert_chore(self, assigned_to: str, due_date: str | None = None) -> int:
        with self.app.state.database.session() as connection:
            cursor = connection.execute(
                """
                INSERT INTO chores (house_id, title, assigned_to, due_date, status)
                VALUES (?, '주방 청소', ?, ?, '진행 전')
                """,
                (self.house_id, assigned_to, due_date or date.today().isoformat()),
            )
            return int(cursor.lastrowid)

    async def test_one_member_house_returns_only_login_user(self) -> None:
        chore_id = self.insert_chore("혼자사용자")
        self.insert_chore("존재하지않는사용자")

        response = await self.client.get(
            f"/houses/{self.house_id}/chores", headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], chore_id)
        self.assertEqual(payload[0]["assignee"]["user_id"], self.auth["user"]["id"])
        self.assertEqual(payload[0]["assignee"]["display_name"], "혼자사용자")

    async def test_empty_house_schedule_returns_empty_list(self) -> None:
        response = await self.client.get(
            f"/houses/{self.house_id}/chores", headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    async def test_member_can_update_valid_chore_status(self) -> None:
        chore_id = self.insert_chore(
            "혼자사용자", (date.today() + timedelta(days=1)).isoformat()
        )
        response = await self.client.patch(
            f"/houses/{self.house_id}/chores/{chore_id}",
            headers=self.headers,
            json={"status": "완료"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "완료")

    async def test_non_member_cannot_read_or_update_chores(self) -> None:
        chore_id = self.insert_chore("혼자사용자")
        signup = await self.client.post(
            "/auth/signup",
            json={
                "email": "outsider@example.com",
                "password": "correct-password",
                "display_name": "외부사용자",
            },
        )
        outsider_headers = {
            "Authorization": f"Bearer {signup.json()['access_token']}"
        }
        read = await self.client.get(
            f"/houses/{self.house_id}/chores", headers=outsider_headers
        )
        update = await self.client.patch(
            f"/houses/{self.house_id}/chores/{chore_id}",
            headers=outsider_headers,
            json={"status": "완료"},
        )
        self.assertEqual(read.status_code, 403)
        self.assertEqual(update.status_code, 403)


if __name__ == "__main__":
    unittest.main()
