# Nazi AI Architecture (Local-First)

## Product boundary

Nazi AI is a single-owner local application. It has no public registration, public user directory, subscription system, or multi-tenant data model.

## Runtime

- Frontend: React + Vite, served at 127.0.0.1:5173 during development.
- Backend: FastAPI, served at 127.0.0.1:8000.
- Database: SQLite file under backend/data/.
- Local media: avatar files under backend/data/media/avatars/ and served only by the local FastAPI process.
- Backups: ZIP archives built from SQLite online snapshots plus local media, with a SHA-256 manifest and validated restore workflow.
- Restore safety: a pre-restore ZIP is saved locally; the previous database and media are rolled back if installation fails.
- AI inference: external provider API through a backend-only adapter. The API key must never be exposed to the browser.

## Core modules (planned)

- personality: companion identity, traits, style, and user-authored prompt.
- prompt: compose system instructions, personality, recent conversation, and retrieved memories.
- chat: sessions, messages, streaming responses, and conversation lifecycle.
- memory: short-term working context, long-term semantic facts, episodic summaries, confirmed preferences, local embeddings, duplicate detection, and owner-reviewed conflict resolution.
- recall: semantic/lexical search across historical chat messages, with local-only indexing and a lexical fallback when the optional model is absent.
- providers: provider-neutral interface for model APIs.
- settings: local model/provider configuration and usage controls.
- storage: local avatar assets, media inventory, and private data paths.
- backup: versioned archive export, checksum validation, SQLite integrity checks, and restore rollback.

## Privacy and safety

- Bind development servers to loopback (127.0.0.1).
- Keep .env, API keys, SQLite files, and private memory data out of Git.
- Show a clear notice when conversation context is sent to an external model provider.
- Provide export and deletion controls for memories and conversation data.
- Treat user-created character prompts as data, not as instructions that can override application safety rules.
