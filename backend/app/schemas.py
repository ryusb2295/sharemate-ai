import re
from datetime import date

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
    owner_id: int | None
    created_at: str
    member_count: int


class HouseJoinRequest(BaseModel):
    invite_code: str = ""


class HouseMemberResponse(BaseModel):
    id: int
    house_id: int
    user_id: int
    display_name: str
    email: str
    role: str
    joined_at: str


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
    user_id: int
    display_name: str


class ChoreResponse(BaseModel):
    id: int
    house_id: int
    title: str
    description: str
    assignee_user_id: int
    scheduled_date: date
    is_completed: bool
    status: str
    completed_at: str | None
    created_by: int | None
    created_at: str
    assignee: ChoreAssigneeResponse


class ChoreCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    assignee_user_id: int = Field(gt=0)
    scheduled_date: date

    @field_validator("title", "description")
    @classmethod
    def normalize_chore_text(cls, value: str) -> str:
        return value.strip()


class ChoreUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    assignee_user_id: int | None = Field(default=None, gt=0)
    scheduled_date: date | None = None

    @field_validator("title", "description")
    @classmethod
    def normalize_optional_chore_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class ChoreCompleteRequest(BaseModel):
    is_completed: bool
