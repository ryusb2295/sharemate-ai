import tempfile
import unittest
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app
from backend.app.receipt_analyzer import (
    ReceiptAnalysisError,
    ReceiptAnalyzer,
    extract_json_from_text,
)


class ReceiptApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "test.db"
        self.app = create_app(
            database_path,
            receipt_analyzer=ReceiptAnalyzer(mode="mock", mock_enabled=True),
        )
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://testserver",
        )

        signup_response = await self.client.post(
            "/auth/signup",
            json={
                "email": "receipt@example.com",
                "password": "correct-password",
                "display_name": "영수증테스터",
            },
        )
        self.token = signup_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        house_response = await self.client.post(
            "/houses",
            headers=self.headers,
            json={"name": "Receipt House", "location": "Sydney"},
        )
        self.house_id = house_response.json()["id"]

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)
        self.temp_directory.cleanup()

    async def test_mock_receipt_analysis_success(self) -> None:
        response = await self.client.post(
            f"/houses/{self.house_id}/receipts/analyze",
            headers=self.headers,
            files={"file": ("receipt.jpg", b"fake-jpeg-content", "image/jpeg")},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["analysis_mode"], "mock")
        self.assertEqual(payload["total"], 12.0)
        self.assertEqual(payload["items"][0]["quantity"], 1.0)

    async def test_upload_validation_and_house_permission(self) -> None:
        text_response = await self.client.post(
            f"/houses/{self.house_id}/receipts/analyze",
            headers=self.headers,
            files={"file": ("receipt.txt", b"not-an-image", "text/plain")},
        )
        self.assertEqual(text_response.status_code, 415)

        empty_response = await self.client.post(
            f"/houses/{self.house_id}/receipts/analyze",
            headers=self.headers,
            files={"file": ("receipt.jpg", b"", "image/jpeg")},
        )
        self.assertEqual(empty_response.status_code, 400)

        forbidden_response = await self.client.post(
            "/houses/99999/receipts/analyze",
            headers=self.headers,
            files={"file": ("receipt.jpg", b"fake-jpeg-content", "image/jpeg")},
        )
        self.assertEqual(forbidden_response.status_code, 403)

    def test_json_extraction_supports_wrapped_response(self) -> None:
        result = extract_json_from_text(
            'Result: {"store_name":"Test","items":[{"name":"Milk","quantity":1,"price":3.5}],"total":3.5}'
        )
        self.assertEqual(result["store_name"], "Test")

    def test_auto_mode_falls_back_only_when_mock_is_explicitly_enabled(self) -> None:
        auto_result = ReceiptAnalyzer(api_key="", mode="auto", mock_enabled=True).analyze(
            b"fake-image", "image/jpeg"
        )
        self.assertEqual(auto_result["analysis_mode"], "mock")
        self.assertIn("OPENAI_API_KEY", auto_result["warning"])

        with self.assertRaises(ReceiptAnalysisError):
            ReceiptAnalyzer(api_key="", mode="auto", mock_enabled=False).analyze(
                b"fake-image", "image/jpeg"
            )

        with self.assertRaises(ReceiptAnalysisError):
            ReceiptAnalyzer(api_key="", mode="openai").analyze(
                b"fake-image", "image/jpeg"
            )


if __name__ == "__main__":
    unittest.main()
