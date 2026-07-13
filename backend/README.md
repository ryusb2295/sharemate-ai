# RoomSync API

## Setup

From the repository root:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m backend.scripts.prepare_database
backend/.venv/Scripts/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

Use `ROOMSYNC_DB_PATH` to select a different SQLite working database. The default
is `backend/data/roomsync.db`; the root Streamlit database is never modified by the
default configuration.

## Cleaning

- `GET /houses/{house_id}/chores`: list only chores assigned to a verified member of that house.
- `PATCH /houses/{house_id}/chores/{chore_id}`: change a verified chore status between `진행 전` and `완료`.

Both endpoints require a bearer session and reject users who are not members of the requested house.

## Receipt analysis

Create `backend/.env` from `.env.example` and configure one of these modes:

- `ROOMSYNC_RECEIPT_MODE=auto`: use OpenAI when a key is present; errors remain errors by default.
- `ROOMSYNC_RECEIPT_MODE=openai`: require OpenAI and return an API error when unavailable.
- `ROOMSYNC_RECEIPT_MODE=mock`: request deterministic demo data.

Mock output is disabled unless `ROOMSYNC_RECEIPT_MOCK_ENABLED=true` is explicitly set.

Set `OPENAI_API_KEY` only in `backend/.env`. Never add it to the Expo environment.

## Tests

```powershell
backend/.venv/Scripts/python -m unittest backend.tests.test_api -v
```
