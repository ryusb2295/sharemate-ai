import os
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATABASE_PATH = PROJECT_ROOT / "sharemate.db"
DEFAULT_DATABASE_PATH = BACKEND_ROOT / "data" / "roomsync.db"
DEFAULT_BACKUP_DIR = BACKEND_ROOT / "backups"

load_dotenv(BACKEND_ROOT / ".env")


def get_database_path() -> Path:
    configured_path = os.getenv("ROOMSYNC_DB_PATH")
    return Path(configured_path).resolve() if configured_path else DEFAULT_DATABASE_PATH


def prepare_database_copy(database_path: Path) -> Path | None:
    """Create a working DB copy and a pre-migration backup without changing the source DB."""
    database_path.parent.mkdir(parents=True, exist_ok=True)

    if not database_path.exists():
        if not SOURCE_DATABASE_PATH.exists():
            raise FileNotFoundError(f"Source database not found: {SOURCE_DATABASE_PATH}")
        shutil.copy2(SOURCE_DATABASE_PATH, database_path)

    with sqlite3.connect(database_path) as connection:
        auth_schema_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'users'"
        ).fetchone()
    if auth_schema_exists:
        return None

    backup_dir = Path(os.getenv("ROOMSYNC_BACKUP_DIR", DEFAULT_BACKUP_DIR))
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"roomsync-before-auth-{timestamp}.db"
    shutil.copy2(database_path, backup_path)
    return backup_path


def get_cors_origins() -> list[str]:
    raw_origins = os.getenv("ROOMSYNC_CORS_ORIGINS", "*")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def get_receipt_mode() -> str:
    mode = os.getenv("ROOMSYNC_RECEIPT_MODE", "auto").strip().lower()
    return mode if mode in {"auto", "openai", "mock"} else "auto"


def get_receipt_mock_enabled() -> bool:
    return os.getenv("ROOMSYNC_RECEIPT_MOCK_ENABLED", "false").strip().lower() == "true"


def get_receipt_model() -> str:
    return os.getenv("ROOMSYNC_RECEIPT_MODEL", "gpt-4.1-mini").strip()
