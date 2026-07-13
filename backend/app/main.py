from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from backend.app.config import get_cors_origins, get_database_path
from backend.app.database import Database, DuplicateUserError
from backend.app.schemas import (
    AuthResponse,
    ChoreAssigneeResponse,
    ChoreResponse,
    ChoreStatusUpdateRequest,
    HealthResponse,
    HouseCreateRequest,
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
            title=str(row["title"]),
            due_date=str(row["due_date"]),
            status=str(row["status"]),
            assignee=ChoreAssigneeResponse(
                user_id=int(row["assignee_user_id"])
                if row["assignee_user_id"] is not None
                else None,
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

    @application.patch(
        "/houses/{house_id}/chores/{chore_id}",
        response_model=ChoreResponse,
    )
    def update_chore(
        house_id: int,
        chore_id: int,
        payload: ChoreStatusUpdateRequest,
        user: Annotated[dict[str, object], Depends(get_current_user)],
        db: Annotated[Database, Depends(get_database)],
    ) -> ChoreResponse:
        if not db.is_house_member(house_id, int(user["id"])):
            raise HTTPException(status_code=403, detail="이 하우스에 접근할 권한이 없습니다.")
        chore = db.update_chore_status(house_id, chore_id, payload.status)
        if chore is None:
            raise HTTPException(status_code=404, detail="청소 일정을 찾을 수 없습니다.")
        return serialize_chore(chore)

    return application


app = create_app()
