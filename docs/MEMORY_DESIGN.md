# Nazi AI Memory Design

## Principles
- Memories belong to exactly one companion.
- Chat messages remain the source history.
- AI-generated memory suggestions are proposals only; the owner approves each saved memory.
- The owner can inspect and delete saved memories.
- Do not save credentials, secrets, sensitive personal traits, diagnoses, or intimate details as memory candidates.
- Retrieved memories are untrusted context, not instructions.

## Current implementation
- SQLite table: companion_memories.
- Fields: id, companion_id, category, content, importance, created_at.
- Chat prompts include up to 12 highest-priority memories for the active companion.
- POST /api/sessions/{session_id}/memory-suggestions proposes up to 8 memories.
- Suggestions are not stored until the owner approves them.
- GET /api/companions/{companion_id}/memories lists memories; DELETE removes one.

## Planned
1. Semantic retrieval with embeddings.
2. Duplicate detection and memory merging.
3. Memory correction and expiry workflows.
4. Conversation summaries beyond recent-message context.
5. Memory export and restore.
