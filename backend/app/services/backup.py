from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

FORMAT_NAME = "nazi-ai-backup"
FORMAT_VERSION = 1
DATABASE_ARCHIVE_PATH = "database/nazi_ai.sqlite3"
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
MAX_DATABASE_BYTES = 512 * 1024 * 1024
MAX_MEDIA_FILE_BYTES = 25 * 1024 * 1024
MAX_ARCHIVE_FILES = 10000
REQUIRED_TABLES = {"companions", "chat_sessions", "messages"}


class BackupValidationError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _media_files(media_directory: Path) -> list[Path]:
    if not media_directory.exists():
        return []
    result: list[Path] = []
    for root, directories, filenames in os.walk(media_directory, followlinks=False):
        directories[:] = [
            name for name in directories
            if not (Path(root) / name).is_symlink()
        ]
        for name in filenames:
            candidate = Path(root) / name
            if candidate.is_file() and not candidate.is_symlink():
                result.append(candidate)
    return sorted(result, key=lambda item: item.as_posix().lower())


def build_backup_archive(
    output_path: Path,
    database_path: Path,
    media_directory: Path,
) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not database_path.is_file():
        raise FileNotFoundError("فایل دیتابیس پیدا نشد؛ ابتدا برنامه را اجرا کن.")

    import tempfile

    with tempfile.TemporaryDirectory(prefix="nazi-ai-backup-") as temporary:
        snapshot_path = Path(temporary) / "nazi_ai.sqlite3"
        source = sqlite3.connect(str(database_path), timeout=30)
        destination = sqlite3.connect(str(snapshot_path), timeout=30)
        try:
            source.backup(destination)
            check = destination.execute("PRAGMA integrity_check").fetchone()
            if not check or check[0] != "ok":
                raise BackupValidationError("سلامت دیتابیس برای پشتیبان‌گیری تأیید نشد.")
        finally:
            destination.close()
            source.close()

        archive_entries: list[tuple[str, Path]] = [
            (DATABASE_ARCHIVE_PATH, snapshot_path)
        ]
        for media_file in _media_files(media_directory):
            relative = media_file.relative_to(media_directory).as_posix()
            archive_entries.append((f"media/{relative}", media_file))

        total_size = sum(path.stat().st_size for _, path in archive_entries)
        if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
            raise BackupValidationError("حجم اطلاعات برای ساخت یک فایل پشتیبان بیش از حد مجاز است.")
        if len(archive_entries) > MAX_ARCHIVE_FILES:
            raise BackupValidationError("تعداد فایل‌ها برای پشتیبان‌گیری بیش از حد مجاز است.")

        manifest_files = []
        for archive_name, file_path in archive_entries:
            size = file_path.stat().st_size
            if archive_name == DATABASE_ARCHIVE_PATH and size > MAX_DATABASE_BYTES:
                raise BackupValidationError("حجم دیتابیس از حد مجاز پشتیبان‌گیری بیشتر است.")
            if archive_name.startswith("media/") and size > MAX_MEDIA_FILE_BYTES:
                raise BackupValidationError(f"فایل رسانه‌ای بیش از حد بزرگ است: {file_path.name}")
            manifest_files.append({
                "path": archive_name,
                "size": size,
                "sha256": _sha256(file_path),
            })

        manifest = {
            "format": FORMAT_NAME,
            "format_version": FORMAT_VERSION,
            "app_name": "Nazi AI",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database": DATABASE_ARCHIVE_PATH,
            "files": manifest_files,
        }
        with zipfile.ZipFile(
            output_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            )
            for archive_name, file_path in archive_entries:
                archive.write(file_path, archive_name)

    return {
        "created_at": manifest["created_at"],
        "media_files": sum(1 for name, _ in archive_entries if name.startswith("media/")),
        "database_bytes": snapshot_path.stat().st_size if snapshot_path.exists() else manifest_files[0]["size"],
        "archive_bytes": output_path.stat().st_size,
    }


def extract_backup_archive(archive_path: Path, staging_directory: Path) -> dict:
    archive_size = archive_path.stat().st_size
    if archive_size <= 0 or archive_size > MAX_ARCHIVE_BYTES:
        raise BackupValidationError("حجم فایل پشتیبان معتبر نیست.")
    staging_directory.mkdir(parents=True, exist_ok=True)

    try:
        archive = zipfile.ZipFile(archive_path, "r")
    except (zipfile.BadZipFile, OSError) as exc:
        raise BackupValidationError("فایل انتخاب‌شده یک پشتیبان ZIP معتبر نیست.") from exc

    with archive:
        infos = archive.infolist()
        if not infos or len(infos) > MAX_ARCHIVE_FILES + 1:
            raise BackupValidationError("ساختار فایل پشتیبان معتبر نیست.")
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise BackupValidationError("فایل پشتیبان شامل مسیرهای تکراری است.")
        if "manifest.json" not in names:
            raise BackupValidationError("فایل manifest در پشتیبان وجود ندارد.")

        manifest_info = archive.getinfo("manifest.json")
        if manifest_info.file_size > 2 * 1024 * 1024:
            raise BackupValidationError("فایل manifest بیش از حد بزرگ است.")
        try:
            manifest = json.loads(archive.read(manifest_info).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BackupValidationError("اطلاعات manifest قابل خواندن نیست.") from exc

        if manifest.get("format") != FORMAT_NAME or manifest.get("format_version") != FORMAT_VERSION:
            raise BackupValidationError("نسخه یا قالب فایل پشتیبان با این برنامه سازگار نیست.")
        if manifest.get("database") != DATABASE_ARCHIVE_PATH:
            raise BackupValidationError("مسیر دیتابیس در فایل پشتیبان معتبر نیست.")

        declared_files = manifest.get("files")
        if not isinstance(declared_files, list) or len(declared_files) > MAX_ARCHIVE_FILES:
            raise BackupValidationError("فهرست فایل‌های پشتیبان معتبر نیست.")
        declared = {}
        for item in declared_files:
            if not isinstance(item, dict):
                raise BackupValidationError("یکی از ورودی‌های manifest معتبر نیست.")
            path = item.get("path")
            if not isinstance(path, str) or path in declared:
                raise BackupValidationError("مسیر فایل در manifest معتبر نیست.")
            declared[path] = item

        if DATABASE_ARCHIVE_PATH not in declared:
            raise BackupValidationError("دیتابیس در فایل پشتیبان وجود ندارد.")
        if set(names) != set(declared) | {"manifest.json"}:
            raise BackupValidationError("فایل پشتیبان شامل فایل‌های تعریف‌نشده است.")

        total_size = 0
        media_count = 0
        for info in infos:
            name = info.filename
            if name == "manifest.json":
                continue
            if "\\" in name or "\x00" in name:
                raise BackupValidationError("مسیر یکی از فایل‌های پشتیبان ناامن است.")
            pure_path = PurePosixPath(name)
            if pure_path.is_absolute() or ".." in pure_path.parts or not pure_path.parts:
                raise BackupValidationError("مسیر یکی از فایل‌های پشتیبان ناامن است.")
            if name != DATABASE_ARCHIVE_PATH and not name.startswith("media/"):
                raise BackupValidationError("فایل ناشناخته‌ای در پشتیبان وجود دارد.")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode) or info.is_dir():
                raise BackupValidationError("فایل‌های پیوندی یا پوشه‌های غیرمجاز در پشتیبان پذیرفته نمی‌شوند.")

            metadata = declared[name]
            expected_size = metadata.get("size")
            expected_hash = metadata.get("sha256")
            if not isinstance(expected_size, int) or expected_size < 0 or expected_size != info.file_size:
                raise BackupValidationError("اندازه یکی از فایل‌های پشتیبان با manifest هم‌خوانی ندارد.")
            if not isinstance(expected_hash, str) or len(expected_hash) != 64:
                raise BackupValidationError("چک‌سام یکی از فایل‌های پشتیبان معتبر نیست.")
            if name == DATABASE_ARCHIVE_PATH and info.file_size > MAX_DATABASE_BYTES:
                raise BackupValidationError("حجم دیتابیس در فایل پشتیبان بیش از حد مجاز است.")
            if name.startswith("media/"):
                media_count += 1
                if info.file_size > MAX_MEDIA_FILE_BYTES:
                    raise BackupValidationError("یکی از فایل‌های رسانه‌ای بیش از حد بزرگ است.")
            total_size += info.file_size
            if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise BackupValidationError("حجم بازشده فایل پشتیبان بیش از حد مجاز است.")

            destination = staging_directory.joinpath(*pure_path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            written = 0
            with archive.open(info, "r") as source, destination.open("wb") as target:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > expected_size:
                        raise BackupValidationError("اندازه واقعی فایل از مقدار اعلام‌شده بیشتر است.")
                    digest.update(chunk)
                    target.write(chunk)
            if written != expected_size or digest.hexdigest() != expected_hash:
                raise BackupValidationError(f"اعتبارسنجی فایل ناموفق بود: {name}")

    database_file = staging_directory / DATABASE_ARCHIVE_PATH
    try:
        connection = sqlite3.connect(str(database_file))
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        companion_count = connection.execute("SELECT COUNT(*) FROM companions").fetchone()[0]
        connection.close()
    except sqlite3.DatabaseError as exc:
        raise BackupValidationError("دیتابیس داخل فایل پشتیبان قابل بازیابی نیست.") from exc
    if not integrity or integrity[0] != "ok" or not REQUIRED_TABLES.issubset(tables):
        raise BackupValidationError("سلامت یا ساختار دیتابیس پشتیبان تأیید نشد.")

    media_directory = staging_directory / "media"
    media_directory.mkdir(parents=True, exist_ok=True)
    return {
        "database_path": database_file,
        "media_directory": media_directory,
        "media_files": media_count,
        "companions": companion_count,
        "created_at": manifest.get("created_at"),
    }
