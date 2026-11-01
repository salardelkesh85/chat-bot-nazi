import hashlib
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.services.backup import (
    BackupValidationError,
    build_backup_archive,
    extract_backup_archive,
)


class BackupArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = self.root / "data" / "nazi_ai.db"
        self.database.parent.mkdir(parents=True)
        connection = sqlite3.connect(self.database)
        connection.executescript(
            """
            CREATE TABLE companions (id TEXT PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE chat_sessions (id TEXT PRIMARY KEY, companion_id TEXT);
            CREATE TABLE messages (id TEXT PRIMARY KEY, session_id TEXT, content TEXT);
            INSERT INTO companions (id, name) VALUES ('companion-1', 'Nazanin');
            """
        )
        connection.commit()
        connection.close()
        self.media = self.root / "data" / "media"
        (self.media / "avatars").mkdir(parents=True)
        (self.media / "avatars" / "avatar.png").write_bytes(b"\x89PNG\r\n\x1a\nlocal-test-image")

    def tearDown(self):
        self.temporary.cleanup()

    def test_backup_round_trip_preserves_database_and_media(self):
        archive = self.root / "backup.zip"
        result = build_backup_archive(archive, self.database, self.media)
        self.assertEqual(result["media_files"], 1)
        extracted = extract_backup_archive(archive, self.root / "restored")
        self.assertEqual(extracted["companions"], 1)
        self.assertEqual(extracted["media_files"], 1)
        connection = sqlite3.connect(extracted["database_path"])
        name = connection.execute("SELECT name FROM companions WHERE id='companion-1'").fetchone()[0]
        connection.close()
        self.assertEqual(name, "Nazanin")
        self.assertEqual(
            (extracted["media_directory"] / "avatars" / "avatar.png").read_bytes(),
            (self.media / "avatars" / "avatar.png").read_bytes(),
        )

    def test_rejects_archive_path_traversal(self):
        archive = self.root / "unsafe.zip"
        database_bytes = b"not-a-real-database"
        escaped_bytes = b"outside"
        manifest = {
            "format": "nazi-ai-backup",
            "format_version": 1,
            "database": "database/nazi_ai.sqlite3",
            "files": [
                {
                    "path": "database/nazi_ai.sqlite3",
                    "size": len(database_bytes),
                    "sha256": hashlib.sha256(database_bytes).hexdigest(),
                },
                {
                    "path": "media/../escaped.txt",
                    "size": len(escaped_bytes),
                    "sha256": hashlib.sha256(escaped_bytes).hexdigest(),
                },
            ],
        }
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("manifest.json", json.dumps(manifest))
            output.writestr("database/nazi_ai.sqlite3", database_bytes)
            output.writestr("media/../escaped.txt", escaped_bytes)
        with self.assertRaises(BackupValidationError):
            extract_backup_archive(archive, self.root / "unsafe-extracted")
        self.assertFalse((self.root / "escaped.txt").exists())


if __name__ == "__main__":
    unittest.main()
