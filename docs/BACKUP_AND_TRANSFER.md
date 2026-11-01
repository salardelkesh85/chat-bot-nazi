# Nazi AI — Backup, Restore, and Windows Transfer

## What a backup contains

The ZIP file created from **Dashboard → پشتیبان و فایل‌ها** contains:
- A consistent SQLite snapshot of all app tables.
- Companion profiles and personality settings.
- Chat sessions and messages.
- Memories, approved preferences, emotional roleplay state, and relationship timeline.
- Local media files stored under `backend/data/media/`.
- A manifest with file sizes and SHA-256 checksums.

The archive does **not** contain `backend/.env`, API keys, local AI model weights, Python environments, or Node packages. These are intentionally kept separate from personal-data backups.

## Create a backup

1. Start Nazi AI.
2. Open **پشتیبان و فایل‌ها** from the sidebar.
3. Select **ساخت و دریافت فایل پشتیبان**.
4. Keep the downloaded `nazi-ai-backup-....zip` somewhere private, such as an external drive.

The archive is generated from a SQLite online backup snapshot so it does not rely on copying a live database file directly.

## Restore a backup

1. Start the target installation.
2. Open **پشتیبان و فایل‌ها**.
3. Select the ZIP file created by Nazi AI.
4. Confirm the replacement.

Restore checks the archive format, file paths, file sizes, SHA-256 hashes, SQLite integrity, and required core tables before changing the current data. It automatically creates a `pre-restore-....zip` safety backup first. If installation of the restored database or media fails, the previous database and media directory are put back.

**Important:** a successful restore replaces the current database and local media. Save a fresh backup first if you want to keep the target computer's current data.

## Move to another Windows computer

1. On the old computer, create a ZIP backup from the app.
2. Copy the project repository to the new computer:
   `git clone https://github.com/salardelkesh85/chat-bot-nazi.git`
3. Install Python 3.11 and Node.js 20 LTS or newer.
4. Run `setup_nazi_ai.bat` from the project folder.
5. Copy your old `backend/.env` to the new installation manually, or configure a new provider key in that file. Never put the API key in the backup ZIP or commit it to GitHub.
6. Run `start_nazi_ai.bat`.
7. Open **پشتیبان و فایل‌ها**, select the ZIP backup, and restore it.

## Optional local AI models

Whisper, Piper voice models, and local embedding weights are separate from the data archive because they can be large and may have their own licenses. If you use them, copy the relevant folders under `backend/models/` to the new computer and follow:
- `docs/LOCAL_VOICE_SETUP.md`
- `docs/LOCAL_TTS_SETUP.md`
- `docs/SEMANTIC_MEMORY.md`

Install optional dependencies only if you use those features:
- `backend/requirements-voice.txt`
- `backend/requirements-embeddings.txt`

## Local privacy

The provided Windows launcher binds the backend and frontend to `127.0.0.1`. The backup contains private conversations and memories; do not upload it to a public repository or share it with anyone you do not trust.
