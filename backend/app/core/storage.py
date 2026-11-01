from pathlib import Path

from app.database import engine

if engine.dialect.name != "sqlite" or not engine.url.database or engine.url.database == ":memory:":
    raise RuntimeError("Nazi AI backup and local media storage require a file-based SQLite database.")

DATABASE_FILE = Path(engine.url.database).resolve()
DATA_DIRECTORY = DATABASE_FILE.parent
MEDIA_DIRECTORY = DATA_DIRECTORY / "media"
AVATAR_DIRECTORY = MEDIA_DIRECTORY / "avatars"
BACKUP_DIRECTORY = DATA_DIRECTORY / "backups"

for directory in (MEDIA_DIRECTORY, AVATAR_DIRECTORY, BACKUP_DIRECTORY):
    directory.mkdir(parents=True, exist_ok=True)
