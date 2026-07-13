from backend.app.config import get_database_path, prepare_database_copy
from backend.app.database import Database


def main() -> None:
    database_path = get_database_path()
    backup_path = prepare_database_copy(database_path)
    Database(database_path).initialize()
    print(f"Working database: {database_path}")
    print(f"Pre-migration backup: {backup_path}")


if __name__ == "__main__":
    main()
