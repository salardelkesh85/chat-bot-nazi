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
- [x] Manually create, edit, re-categorize, re-rank, and delete saved memories
- [x] Refresh local semantic embeddings when a memory's text is edited
- [x] Validate partial memory updates and importance bounds
- [x] Optional local multilingual embedding pipeline and semantic retrieval fallback
- [ ] Bundle and verify local embedding model weights on target Windows machine
- [x] User-triggered persistent summaries for individual chat sessions
- [x] Inject up to five earlier session summaries into future chats with the same companion
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
- [x] Suggest shared-story events from user-authored chat messages for explicit review
- [x] Inject confirmed relationship timeline events into future companion prompts
- [x] Per-companion confirmed communication preference profile
- [x] Suggest communication preferences from explicit user statements; require confirmation before saving
- [x] Inject confirmed preferences into future chat prompts
- [x] Preference profile UI with manual add and delete
- [x] Preference suggestions and shared-event suggestions reviewed separately in chat
- [ ] User-editable preference values and conflict-resolution workflow
- [ ] More robust multilingual sentiment and context analysis

## Phase 5 — Advanced experience
- [x] Companion avatar URL field and preview in create/edit studio
- [ ] Local image upload and local image management
- [ ] Streaming chat responses
- [x] Browser-based Persian text-to-speech playback for assistant messages
- [x] Per-chat speech rate and pitch controls
- [x] Browser SpeechRecognition microphone input with Persian fa-IR recognition
- [x] Optional local faster-whisper transcription API with 20 MB upload cap
- [x] Local microphone recording UI that sends audio only to the local backend
- [x] Windows setup guide for offline model loading
- [x] Optional automatic speech playback after AI replies
- [ ] Fully offline local speech-to-text engine (replace browser-dependent recognition)
- [x] Local Piper TTS adapter and synthesis endpoint
- [x] Per-companion local voice selection stored in personality configuration
- [x] Local WAV playback and automatic local-voice preference when selected
- [ ] Validate and select a high-quality Persian Piper voice model on the target Windows laptop
- [ ] Offline local neural TTS performance and quality tuning
- [ ] Local backup and restore workflow
- [ ] Usage and latency diagnostics

## Phase 6 — Reliability
- [ ] Automated backend and frontend tests
- [ ] Windows launch scripts
- [ ] Dependency lockfiles
- [ ] Local installation and smoke test
