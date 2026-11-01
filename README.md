# Nazi AI — Local Personal AI Companion

A private, single-owner AI companion application designed to run locally on your Windows computer.

## Current status

Current implementation:
- React + Vite frontend
- FastAPI backend
- SQLite local database
- Local-only development endpoints
- Companion creation and editing API
- Persistent chat sessions and message history
- OpenAI-compatible API adapter
- Per-companion saved memory CRUD and memory context injection
- AI memory suggestions with owner approval
- Lightweight local relevance ranking with optional multilingual local vector embeddings
- Conversation history and resume
- No public registration or multi-user system

## Requirements

- Windows 10/11
- Python 3.11+
- Node.js 20 LTS+

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

## Local semantic memory

The backend supports optional on-device multilingual embeddings. Install `backend/requirements-embeddings.txt` and place the model files in `backend/models/paraphrase-multilingual-MiniLM-L12-v2`. The app uses local-only model loading and falls back to keyword retrieval if the model is not installed. See [docs/SEMANTIC_MEMORY.md](docs/SEMANTIC_MEMORY.md). The first-time model acquisition is a separate manual step; model weights are excluded from Git.

## Planned modules

1. Companion/personality creator
2. Chat and conversation history
3. Long-term memory and local semantic/lexical retrieval
4. AI provider adapters
5. Local settings, export, and backup

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/ROADMAP.md](docs/ROADMAP.md).
