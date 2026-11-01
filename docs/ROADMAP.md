# Nazi AI Roadmap

## Phase 1 — Foundation
- [x] Repository scaffold
- [x] React + Vite local frontend
- [x] FastAPI local backend
- [x] SQLite database initialization
- [x] Local health endpoint

## Phase 2 — Companion creation and chat
- [x] Companion data model and CRUD API
- [x] Personality fields and custom prompt
- [x] Persistent chat sessions and messages
- [x] OpenAI-compatible provider adapter
- [x] Frontend companion creator and chat UI
- [x] Edit companion name, age, description, traits, interests, and personality prompt from the dashboard
- [x] Conversation history and resume
- [ ] Verify provider configuration and chat locally

## Phase 3 — Memory foundation
- [x] Per-companion memory storage
- [x] Memory list and delete APIs
- [x] Memory context injected into chat prompts
- [x] AI-generated memory suggestions
- [x] Explicit user approval before saving suggested memories
- [x] Memory vault UI
- [x] Optional local multilingual embedding pipeline and semantic retrieval fallback
- [ ] Bundle and verify local embedding model weights on target Windows machine
- [ ] Automatic conversation summaries
- [ ] Background memory consolidation

## Phase 4 — Character behavior
- [x] Per-companion fictional state record (mood, familiarity, trust, energy)
- [x] Gradual bounded state updates from conversation cues
- [x] Include state in character prompt context
- [x] Display state indicators in chat UI
- [x] User-adjustable behavior sliders and personality presets
- [x] Personality presets: gentle, playful, romantic, serious, and custom
- [x] Structured voice style and character backstory settings
- [x] Apply personality configuration consistently in chat prompt
- [x] Per-companion relationship timeline storage and CRUD API
- [x] Manually curated milestones and shared memories in the frontend
- [ ] More robust multilingual sentiment and context analysis

## Phase 5 — Advanced experience
- [ ] Avatar upload and local image management
- [ ] Streaming chat responses
- [ ] Voice input/output
- [ ] Local backup and restore workflow
- [ ] Usage and latency diagnostics

## Phase 6 — Reliability
- [ ] Automated backend and frontend tests
- [ ] Windows launch scripts
- [ ] Dependency lockfiles
- [ ] Local installation and smoke test
