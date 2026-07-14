from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from backend.app.config import get_cors_origins, get_database_path
from backend.app.database import (
    AlreadyHouseMemberError,
    Database,
    DuplicateUserError,
    HouseNotFoundError,
)
from backend.app.schemas import (
    AuthResponse,
    ChoreAssigneeResponse,
    ChoreCompleteRequest,
    ChoreCreateRequest,
    ChoreResponse,
    ChoreUpdateRequest,
    HealthResponse,
    HouseCreateRequest,
    HouseJoinRequest,
    HouseMemberResponse,
    HouseResponse,
    LoginRequest,
    ReceiptAnalysisResponse,
    SignupRequest,
    UserResponse,
)
from backend.app.receipt_analyzer import ReceiptAnalysisError, ReceiptAnalyzer
from backend.app.security import create_access_token, hash_password, verify_password

bearer_scheme = HTTPBearer(auto_error=False)


MAX_RECEIPT_BYTES = 10 * 1024 * 1024


def create_app(
    database_path: Path | None = None,
    receipt_analyzer: ReceiptAnalyzer | None = None,
) -> FastAPI:
    database = Database(database_path or get_database_path())
    analyzer = receipt_analyzer or ReceiptAnalyzer()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database.initialize()
        application.state.database = database
        application.state.receipt_analyzer = analyzer
        yield

    application = FastAPI(
        title="RoomSync API",
        version="0.1.0",
        lifespan=lifespan,
    )
    origins = get_cors_origins()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_database(request: Request) -> Database:
        return request.app.state.database

    def get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
        db: Annotated[Database, Depends(get_database)],
    ) -> dict[str, object]:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")
        user = db.get_user_by_token(credentials.credentials)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="로그인 세션이 만료되었습니다.",
            )
        return user

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.post("/auth/signup", response_model=AuthResponse, status_code=201)
    def signup(payload: SignupRequest, db: Annotated[Database, Depends(get_database)]) -> AuthResponse:
        try:
            user = db.create_user(
                email=payload.email,
                password_hash=hash_password(payload.password),
                display_name=payload.display_name,
            )
        except DuplicateUserError as error:
            detail = "이미 가입된 이메일입니다." if error.field == "email" else "이미 사용 중인 이름입니다."
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from error

        token = create_access_token()
        db.create_session(int(user["id"]), token)
        return AuthResponse(access_token=token, user=UserResponse(**user))

    @application.post("/auth/login", response_model=AuthResponse)
    def login(payload: LoginRequest, db: Annotated[Database, Depends(get_database)]) -> AuthResponse:
        user = db.get_user_with_password(payload.email)
        if user is None or not verify_password(payload.password, str(user["password_hash"])):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            )

        token = create_access_token()
        db.create_session(int(user["id"]), token)
        public_user = UserResponse(
            id=int(user["id"]),
            email=str(user["email"]),
            display_name=str(user["display_name"]),
        )
        return AuthResponse(access_token=token, user=public_user)

    @application.get("/auth/me", response_model=UserResponse)
    def me(user: Annotated[dict[str, object], Depends(get_current_user)]) -> UserResponse:
        return UserResponse(**user)

    @application.post("/auth/logout", status_code=204)
    def logout(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
        db: Annotated[Database, Depends(get_database)],
        _: Annotated[dict[str, object], Depends(get_current_user)],
    ) -> None:
        if credentials:
            db.delete_session(credentials.credentials)

    @application.get("/houses", response_model=list[HouseResponse])
    def list_houses(
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> list[HouseResponse]:
        houses = db.list_houses(int(user["id"]))
        return [HouseResponse(**house) for house in houses]

    @application.post("/houses", response_model=HouseResponse, status_code=201)
    def create_house(
        payload: HouseCreateRequest,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> HouseResponse:
        try:
            house = db.create_house(
                payload.name,
                payload.location,
                int(user["id"]),
                str(user["display_name"]),
            )
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return HouseResponse(**house)

    @application.post("/houses/join", response_model=HouseResponse)
    def join_house(
        payload: HouseJoinRequest,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> HouseResponse:
        invite_code = "".join(payload.invite_code.split()).upper()
        if not invite_code:
            raise HTTPException(status_code=400, detail="초대코드를 입력해주세요.")
        if not (6 <= len(invite_code) <= 8 and invite_code.isalnum() and invite_code.isascii()):
            raise HTTPException(
                status_code=400,
                detail="초대코드는 6~8자리 영문 대문자와 숫자 조합입니다.",
            )
        try:
            house = db.join_house_by_invite(
                invite_code,
                int(user["id"]),
                str(user["display_name"]),
            )
        except HouseNotFoundError as error:
            raise HTTPException(status_code=404, detail="초대코드에 해당하는 하우스가 없습니다.") from error
        except AlreadyHouseMemberError as error:
            raise HTTPException(status_code=409, detail="이미 참여 중인 하우스입니다.") from error
        return HouseResponse(**house)

    @application.get("/houses/{house_id}", response_model=HouseResponse)
    def get_house(
        house_id: int,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> HouseResponse:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")
        house = db.get_house(house_id, int(user["id"]))
        if house is None:
            raise HTTPException(status_code=404, detail="하우스를 찾을 수 없습니다.")
        return HouseResponse(**house)

    @application.get(
        "/houses/{house_id}/members",
        response_model=list[HouseMemberResponse],
    )
    def list_house_members(
        house_id: int,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> list[HouseMemberResponse]:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")
        return [
            HouseMemberResponse(**member)
            for member in db.list_house_members(house_id)
        ]

    @application.post(
        "/houses/{house_id}/receipts/analyze",
        response_model=ReceiptAnalysisResponse,
    )
    async def analyze_receipt(
        house_id: int,
        file: UploadFile,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
        request: Request,
    ) -> ReceiptAnalysisResponse:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")

        mime_type = (file.content_type or "").lower()
        if not mime_type.startswith("image/"):
            raise HTTPException(status_code=415, detail="이미지 파일만 업로드할 수 있습니다.")

        image_bytes = await file.read(MAX_RECEIPT_BYTES + 1)
        await file.close()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="업로드한 이미지가 비어 있습니다.")
        if len(image_bytes) > MAX_RECEIPT_BYTES:
            raise HTTPException(status_code=413, detail="이미지 크기는 10MB 이하여야 합니다.")

        try:
            result = await run_in_threadpool(
                request.app.state.receipt_analyzer.analyze,
                image_bytes,
                mime_type,
            )
        except ReceiptAnalysisError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return ReceiptAnalysisResponse(**result)

    def serialize_chore(row: dict[str, object]) -> ChoreResponse:
        return ChoreResponse(
            id=int(row["id"]),
            house_id=int(row["house_id"]),
            title=str(row["title"]),
            description=str(row["description"]),
            assignee_user_id=int(row["assignee_user_id"]),
            scheduled_date=str(row["scheduled_date"]),
            is_completed=str(row["status"]) == "완료",
            status=str(row["status"]),
            completed_at=str(row["completed_at"])
            if row["completed_at"] is not None
            else None,
            created_by=int(row["created_by"])
            if row["created_by"] is not None
            else None,
            created_at=str(row["created_at"]),
            assignee=ChoreAssigneeResponse(
                user_id=int(row["assignee_user_id"]),
                display_name=str(row["assignee_display_name"]),
            ),
        )

    @application.get("/houses/{house_id}/chores", response_model=list[ChoreResponse])
    def list_chores(
        house_id: int,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> list[ChoreResponse]:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")
        return [serialize_chore(row) for row in db.list_validated_chores(house_id)]

    @application.post(
        "/houses/{house_id}/chores",
        response_model=ChoreResponse,
        status_code=201,
    )
    def create_chore(
        house_id: int,
        payload: ChoreCreateRequest,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> ChoreResponse:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")
        if not payload.title:
            raise HTTPException(status_code=400, detail="청소 항목명을 입력해주세요.")
        if not db.is_house_member(house_id, payload.assignee_user_id):
            raise HTTPException(status_code=400, detail="담당자는 현재 하우스 멤버여야 합니다.")
        chore = db.create_chore(
            house_id=house_id,
            title=payload.title,
            description=payload.description,
            assignee_user_id=payload.assignee_user_id,
            scheduled_date=payload.scheduled_date.isoformat(),
            created_by=int(user["id"]),
        )
        if chore is None:
            raise HTTPException(status_code=400, detail="담당자 정보를 확인해주세요.")
        return serialize_chore(chore)

    @application.patch(
        "/houses/{house_id}/chores/{chore_id}",
        response_model=ChoreResponse,
    )
    def update_chore(
        house_id: int,
        chore_id: int,
        payload: ChoreUpdateRequest,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> ChoreResponse:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")
        changes: dict[str, object] = {}
        for field in payload.model_fields_set:
            value = getattr(payload, field)
            if value is not None:
                changes[field] = value.isoformat() if field == "scheduled_date" else value
        if not changes:
            raise HTTPException(status_code=400, detail="수정할 내용을 입력해주세요.")
        if "title" in changes and not str(changes["title"]):
            raise HTTPException(status_code=400, detail="청소 항목명을 입력해주세요.")
        if "assignee_user_id" in changes and not db.is_house_member(
            house_id, int(changes["assignee_user_id"])
        ):
            raise HTTPException(status_code=400, detail="담당자는 현재 하우스 멤버여야 합니다.")
        chore = db.update_chore(house_id, chore_id, changes)
        if chore is None:
            raise HTTPException(status_code=404, detail="청소 일정을 찾을 수 없습니다.")
        return serialize_chore(chore)

    @application.patch(
        "/houses/{house_id}/chores/{chore_id}/complete",
        response_model=ChoreResponse,
    )
    def complete_chore(
        house_id: int,
        chore_id: int,
        payload: ChoreCompleteRequest,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> ChoreResponse:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")
        chore = db.set_chore_completion(house_id, chore_id, payload.is_completed)
        if chore is None:
            raise HTTPException(status_code=404, detail="청소 일정을 찾을 수 없습니다.")
        return serialize_chore(chore)

    @application.delete(
        "/houses/{house_id}/chores/{chore_id}",
        status_code=204,
    )
    def delete_chore(
        house_id: int,
        chore_id: int,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> None:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")
        if not db.delete_chore(house_id, chore_id):
            raise HTTPException(status_code=404, detail="청소 일정을 찾을 수 없습니다.")

    return application


app = create_app()
