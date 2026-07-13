import tempfile
import unittest
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app


class RoomSyncApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "test.db"
        self.app = create_app(database_path)
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)
        self.temp_directory.cleanup()

    async def signup(self) -> dict[str, object]:
        response = await self.client.post(
            "/auth/signup",
            json={
                "email": "member@example.com",
                "password": "correct-password",
                "display_name": "테스트사용자",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    async def test_health(self) -> None:
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    async def test_signup_session_and_duplicate_errors(self) -> None:
        auth = await self.signup()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}

        me_response = await self.client.get("/auth/me", headers=headers)
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["email"], "member@example.com")

        duplicate_response = await self.client.post(
            "/auth/signup",
            json={
                "email": "member@example.com",
                "password": "another-password",
                "display_name": "다른이름",
            },
        )
        self.assertEqual(duplicate_response.status_code, 409)

        duplicate_name_response = await self.client.post(
            "/auth/signup",
            json={
                "email": "other@example.com",
                "password": "another-password",
                "display_name": "테스트사용자",
            },
        )
        self.assertEqual(duplicate_name_response.status_code, 409)

    async def test_login_success_and_failure(self) -> None:
        await self.signup()

        failed_response = await self.client.post(
            "/auth/login",
            json={"email": "member@example.com", "password": "wrong-password"},
        )
        self.assertEqual(failed_response.status_code, 401)

        success_response = await self.client.post(
            "/auth/login",
            json={"email": "member@example.com", "password": "correct-password"},
        )
        self.assertEqual(success_response.status_code, 200)
        self.assertIn("access_token", success_response.json())

    async def test_house_empty_create_and_list(self) -> None:
        auth = await self.signup()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}

        empty_response = await self.client.get("/houses", headers=headers)
        self.assertEqual(empty_response.status_code, 200)
        self.assertEqual(empty_response.json(), [])

        create_response = await self.client.post(
            "/houses",
            headers=headers,
            json={"name": "Sydney House", "location": "Sydney"},
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.json()["member_count"], 1)

        list_response = await self.client.get("/houses", headers=headers)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.json()[0]["name"], "Sydney House")

    async def test_authentication_is_required(self) -> None:
        response = await self.client.get("/houses")
        self.assertEqual(response.status_code, 401)

    async def test_logout_invalidates_session(self) -> None:
        auth = await self.signup()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}

        logout_response = await self.client.post("/auth/logout", headers=headers)
        self.assertEqual(logout_response.status_code, 204)

        me_response = await self.client.get("/auth/me", headers=headers)
        self.assertEqual(me_response.status_code, 401)

    async def test_invalid_signup_and_house_inputs(self) -> None:
        signup_response = await self.client.post(
            "/auth/signup",
            json={"email": "not-an-email", "password": "short", "display_name": "A"},
        )
        self.assertEqual(signup_response.status_code, 422)

        auth = await self.signup()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        house_response = await self.client.post(
            "/houses", headers=headers, json={"name": "Hi", "location": ""}
        )
        self.assertEqual(house_response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
