# Nazi AI — Local Personal AI Companion

A private, single-owner AI companion application designed to run locally on your Windows computer.

## Current status

Current implementation:
- React + Vite frontend
- FastAPI backend
- SQLite local database
- Local-only development endpoints
- Companion creation and editing API
- Personality Studio with presets and behavior sliders
- Persistent chat sessions and message history
- OpenAI-compatible API adapter
- Optional local speech-to-text through faster-whisper (model weights installed separately)
- Optional per-companion local Piper text-to-speech with WAV playback
- Per-companion saved memory CRUD and memory context injection
- AI memory suggestions with owner approval
- Persistent per-session conversation summaries and cross-session context injection
- Per-companion approved preference profiles and user-reviewed character evolution suggestions
- Shared relationship timeline context injected into future chats
- Layered short-term, semantic, episodic, and preference memory
- Semantic/lexical recall across all earlier chat sessions, with local reindexing
- Duplicate and possible contradiction checks with explicit owner review
- Consistent SQLite ZIP backup with SHA-256 manifest validation and safe restore rollback
- Local avatar image upload, static serving, replacement, deletion, and media inventory
- Local backup and restore dashboard with transfer guidance
- Lightweight local relevance ranking with optional multilingual local vector embeddings
- Conversation history and resume
- No public registration or multi-user system

## Requirements

- Windows 10/11
- Python 3.11 or 3.12 (recommended)
- Node.js 20 LTS or 22 LTS
- Ollama (optional, recommended for fully local chat)

## Windows quick start

1. Install Python 3.11/3.12 and Node.js 20/22 LTS.
2. For local AI, install Ollama from https://ollama.com/download/windows and run `ollama pull qwen2.5:3b` in a terminal. This is a lighter starter model; a larger model can be selected later if the laptop has enough RAM.
3. Run `setup_nazi_ai.bat` once.
4. Run `start_nazi_ai.bat`. It waits for both services to pass health checks before opening the app.
5. Use `stop_nazi_ai.bat` to stop the local services when finished.
6. If Ollama is not installed, the dashboard and local database still run; chat generation remains unavailable until a provider is configured.

See [docs/BACKUP_AND_TRANSFER.md](docs/BACKUP_AND_TRANSFER.md) for backup and computer migration instructions.

## Run the backend

Open PowerShell in the repository:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend health: http://127.0.0.1:8000/api/health

## Run the frontend

Open a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173

## Local privacy

- The backend binds to 127.0.0.1, not the public network.
- SQLite data is stored under `backend/data/nazi_ai.db`.
- Never commit `.env`, API keys, the database, or private memories.
- When an external AI API is configured, message context sent for inference leaves the computer and is processed by that provider.

## Local voice engine

Install `backend/requirements-voice.txt` and follow [docs/LOCAL_VOICE_SETUP.md](docs/LOCAL_VOICE_SETUP.md) to enable local faster-whisper transcription. Model weights are not stored in Git and are never downloaded at runtime. Chat completion remains independently configurable.

## Local voice output

Install Piper and a compatible local ONNX voice model, then follow [docs/LOCAL_TTS_SETUP.md](docs/LOCAL_TTS_SETUP.md). Each companion can store its own selected local voice. No voice model is bundled or downloaded at runtime.

## Local AI with Ollama

The default Windows environment example is configured for Ollama at `http://127.0.0.1:11434/v1`, with no API key. Install Ollama, pull the model named by `AI_MODEL` in `backend/.env`, and keep the Ollama service running while chatting. For lower-memory laptops, choose a smaller Ollama model and update `AI_MODEL`. The app can also connect to a cloud OpenAI-compatible provider; in that case, prompts and selected memories are sent to that provider.

## Local semantic memory

The backend supports optional on-device multilingual embeddings. Install `backend/requirements-embeddings.txt` and place the model files in `backend/models/paraphrase-multilingual-MiniLM-L12-v2`. The app uses local-only model loading and falls back to keyword retrieval if the model is not installed. See [docs/SEMANTIC_MEMORY.md](docs/SEMANTIC_MEMORY.md). The first-time model acquisition is a separate manual step; model weights are excluded from Git.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/MEMORY_SYSTEM.md](docs/MEMORY_SYSTEM.md), and [docs/ROADMAP.md](docs/ROADMAP.md).
