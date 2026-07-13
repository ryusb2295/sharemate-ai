import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=40)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("올바른 이메일 주소를 입력해주세요.")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("이름은 2자 이상 입력해주세요.")
        return normalized


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class HouseCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    location: str = Field(min_length=1, max_length=120)

    @field_validator("name", "location")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class HouseResponse(BaseModel):
    id: int
    name: str
    location: str
    invite_code: str
    created_by: str
    member_count: int


class HealthResponse(BaseModel):
    status: str


class ReceiptItemResponse(BaseModel):
    name: str
    quantity: float = Field(default=1, gt=0)
    price: float


class ReceiptAnalysisResponse(BaseModel):
    store_name: str
    items: list[ReceiptItemResponse]
    total: float
    analysis_mode: str
    warning: str | None = None


class ChoreAssigneeResponse(BaseModel):
    user_id: int | None
    display_name: str


class ChoreResponse(BaseModel):
    id: int
    title: str
    due_date: str
    status: str
    assignee: ChoreAssigneeResponse


class ChoreStatusUpdateRequest(BaseModel):
    status: Literal["진행 전", "완료"]
