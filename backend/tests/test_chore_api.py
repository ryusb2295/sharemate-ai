import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app


class ChoreApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "test.db"
        await self.start_app()
        self.owner = await self.signup("owner@example.com", "사용자A")
        self.member = await self.signup("member@example.com", "사용자B")
        house_response = await self.client.post(
            "/houses",
            headers=self.headers(self.owner),
            json={"name": "House A", "location": "Sydney"},
        )
        self.assertEqual(house_response.status_code, 201)
        self.house = house_response.json()
        join_response = await self.client.post(
            "/houses/join",
            headers=self.headers(self.member),
            json={"invite_code": self.house["invite_code"]},
        )
        self.assertEqual(join_response.status_code, 200)

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

    async def create_chore(self) -> dict[str, object]:
        response = await self.client.post(
            f"/houses/{self.house['id']}/chores",
            headers=self.headers(self.owner),
            json={
                "title": "욕실 청소",
                "description": "세면대와 바닥 청소",
                "assignee_user_id": self.member["user"]["id"],
                "scheduled_date": date.today().isoformat(),
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    async def test_empty_create_shared_read_and_restart_persistence(self) -> None:
        empty = await self.client.get(
            f"/houses/{self.house['id']}/chores",
            headers=self.headers(self.owner),
        )
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json(), [])

        created = await self.create_chore()
        self.assertEqual(created["house_id"], self.house["id"])
        self.assertEqual(created["assignee"]["display_name"], "사용자B")
        self.assertFalse(created["is_completed"])

        member_list = await self.client.get(
            f"/houses/{self.house['id']}/chores",
            headers=self.headers(self.member),
        )
        self.assertEqual(member_list.status_code, 200)
        self.assertEqual(member_list.json()[0]["id"], created["id"])

        await self.stop_app()
        await self.start_app()
        login = await self.client.post(
            "/auth/login",
            json={"email": "member@example.com", "password": "correct-password"},
        )
        persisted = await self.client.get(
            f"/houses/{self.house['id']}/chores",
            headers=self.headers(login.json()),
        )
        self.assertEqual(persisted.status_code, 200)
        self.assertEqual(persisted.json()[0]["title"], "욕실 청소")

    async def test_complete_uncomplete_update_and_delete(self) -> None:
        chore = await self.create_chore()
        complete = await self.client.patch(
            f"/houses/{self.house['id']}/chores/{chore['id']}/complete",
            headers=self.headers(self.member),
            json={"is_completed": True},
        )
        self.assertEqual(complete.status_code, 200)
        self.assertTrue(complete.json()["is_completed"])
        self.assertIsNotNone(complete.json()["completed_at"])

        scheduled_date = (date.today() + timedelta(days=1)).isoformat()
        update = await self.client.patch(
            f"/houses/{self.house['id']}/chores/{chore['id']}",
            headers=self.headers(self.owner),
            json={
                "title": "주방 청소",
                "description": "싱크대 포함",
                "assignee_user_id": self.owner["user"]["id"],
                "scheduled_date": scheduled_date,
            },
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["title"], "주방 청소")
        self.assertEqual(update.json()["assignee_user_id"], self.owner["user"]["id"])
        self.assertEqual(update.json()["scheduled_date"], scheduled_date)

        uncomplete = await self.client.patch(
            f"/houses/{self.house['id']}/chores/{chore['id']}/complete",
            headers=self.headers(self.owner),
            json={"is_completed": False},
        )
        self.assertFalse(uncomplete.json()["is_completed"])
        self.assertIsNone(uncomplete.json()["completed_at"])

        delete = await self.client.delete(
            f"/houses/{self.house['id']}/chores/{chore['id']}",
            headers=self.headers(self.member),
        )
        self.assertEqual(delete.status_code, 204)
        remaining = await self.client.get(
            f"/houses/{self.house['id']}/chores",
            headers=self.headers(self.owner),
        )
        self.assertEqual(remaining.json(), [])

    async def test_assignee_and_house_permissions_are_enforced(self) -> None:
        outsider = await self.signup("outside@example.com", "외부사용자")
        invalid_assignee = await self.client.post(
            f"/houses/{self.house['id']}/chores",
            headers=self.headers(self.owner),
            json={
                "title": "잘못된 일정",
                "description": "",
                "assignee_user_id": outsider["user"]["id"],
                "scheduled_date": date.today().isoformat(),
            },
        )
        self.assertEqual(invalid_assignee.status_code, 400)

        chore = await self.create_chore()
        forbidden_read = await self.client.get(
            f"/houses/{self.house['id']}/chores",
            headers=self.headers(outsider),
        )
        forbidden_update = await self.client.patch(
            f"/houses/{self.house['id']}/chores/{chore['id']}",
            headers=self.headers(outsider),
            json={"title": "변경 시도"},
        )
        forbidden_complete = await self.client.patch(
            f"/houses/{self.house['id']}/chores/{chore['id']}/complete",
            headers=self.headers(outsider),
            json={"is_completed": True},
        )
        forbidden_delete = await self.client.delete(
            f"/houses/{self.house['id']}/chores/{chore['id']}",
            headers=self.headers(outsider),
        )
        self.assertEqual(forbidden_read.status_code, 403)
        self.assertEqual(forbidden_update.status_code, 403)
        self.assertEqual(forbidden_complete.status_code, 403)
        self.assertEqual(forbidden_delete.status_code, 403)

        other_house = await self.client.post(
            "/houses",
            headers=self.headers(outsider),
            json={"name": "House B", "location": "Melbourne"},
        )
        other_list = await self.client.get(
            f"/houses/{other_house.json()['id']}/chores",
            headers=self.headers(outsider),
        )
        self.assertEqual(other_list.json(), [])

    async def test_authentication_is_required(self) -> None:
        create = await self.client.post(
            f"/houses/{self.house['id']}/chores",
            json={
                "title": "욕실 청소",
                "description": "",
                "assignee_user_id": self.owner["user"]["id"],
                "scheduled_date": date.today().isoformat(),
            },
        )
        read = await self.client.get(f"/houses/{self.house['id']}/chores")
        self.assertEqual(create.status_code, 401)
        self.assertEqual(read.status_code, 401)


if __name__ == "__main__":
    unittest.main()
