import base64
import json
import logging
import os
import re
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from backend.app.config import get_receipt_mock_enabled, get_receipt_mode, get_receipt_model

logger = logging.getLogger(__name__)


class ReceiptAnalysisError(Exception):
    pass


class ParsedReceiptItem(BaseModel):
    name: str
    quantity: float = Field(default=1, gt=0)
    price: float


class ParsedReceipt(BaseModel):
    store_name: str = "Unknown Store"
    items: list[ParsedReceiptItem]
    total: float


def get_mock_receipt_data(warning: str | None = None) -> dict[str, Any]:
    return {
        "store_name": "Sample Receipt",
        "items": [
            {"name": "MATCHA GELATO SINGLE", "quantity": 1, "price": 15.0},
            {"name": "Discount", "quantity": 1, "price": -3.0},
        ],
        "total": 12.0,
        "analysis_mode": "mock",
        "warning": warning or "Mock 분석 모드로 예시 결과를 표시합니다.",
    }


def extract_json_from_text(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ReceiptAnalysisError("OpenAI 응답에서 JSON을 찾을 수 없습니다.")

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as error:
        raise ReceiptAnalysisError("OpenAI 응답의 JSON 형식이 올바르지 않습니다.") from error
    if not isinstance(parsed, dict):
        raise ReceiptAnalysisError("OpenAI 분석 결과가 객체 형식이 아닙니다.")
    return parsed


class ReceiptAnalyzer:
    def __init__(
        self,
        api_key: str | None = None,
        mode: str | None = None,
        model: str | None = None,
        mock_enabled: bool | None = None,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.mode = mode or get_receipt_mode()
        self.model = model or get_receipt_model()
        self.mock_enabled = mock_enabled if mock_enabled is not None else get_receipt_mock_enabled()

    def analyze(self, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
        if self.mode == "mock":
            if not self.mock_enabled:
                raise ReceiptAnalysisError(
                    "Mock 분석을 사용하려면 ROOMSYNC_RECEIPT_MOCK_ENABLED=true가 필요합니다."
                )
            return get_mock_receipt_data()

        if not self.api_key:
            message = "OPENAI_API_KEY가 없어 Mock 분석 결과를 표시합니다."
            if self.mode == "auto" and self.mock_enabled:
                return get_mock_receipt_data(message)
            raise ReceiptAnalysisError("OpenAI API 키가 설정되지 않았습니다.")

        try:
            return self._analyze_with_openai(image_bytes, mime_type)
        except Exception as error:
            logger.exception("OpenAI receipt analysis failed")
            if self.mode == "auto" and self.mock_enabled:
                return get_mock_receipt_data(
                    "OpenAI 분석을 사용할 수 없어 Mock 분석 결과를 표시합니다."
                )
            if isinstance(error, ReceiptAnalysisError):
                raise
            raise ReceiptAnalysisError("OpenAI 영수증 분석에 실패했습니다.") from error

    def _analyze_with_openai(self, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": """
You are an OCR assistant for receipts.

Analyze the receipt image and return only valid JSON with:
- store_name
- items
- quantity for each item
- price for each item line
- total

Rules:
1. Do not include markdown or explanations.
2. Use numbers only for quantity, price, and total.
3. The price is the full line amount for that quantity.
4. If quantity is not printed, use 1.
5. Include discounts as items with a negative price.
6. If the store is unclear, use "Unknown Store".
7. Keep the item sum close to the receipt total when possible.

Format:
{
  "store_name": "",
  "items": [
    {"name": "", "quantity": 1, "price": 0.00}
  ],
  "total": 0.00
}
""",
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:{mime_type};base64,{base64_image}",
                        },
                    ],
                }
            ],
        )

        parsed_json = extract_json_from_text(response.output_text)
        try:
            parsed_receipt = ParsedReceipt.model_validate(parsed_json)
        except ValidationError as error:
            raise ReceiptAnalysisError("OpenAI 분석 결과에 필요한 항목이 없습니다.") from error

        if not parsed_receipt.items:
            raise ReceiptAnalysisError("분석된 영수증 품목이 없습니다.")

        return {
            **parsed_receipt.model_dump(),
            "analysis_mode": "openai",
            "warning": None,
        }
