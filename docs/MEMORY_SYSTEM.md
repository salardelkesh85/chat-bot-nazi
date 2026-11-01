# Nazi AI — Layered Memory and Historical Recall

## Memory layers

Nazi AI keeps different kinds of context separate instead of treating every old message as a permanent fact.

1. **Short-term working memory** — the most recent 24 messages in the active chat session.
2. **Long-term semantic memory** — user-approved durable facts and context saved in the Memory Vault.
3. **Episodic memory** — important events, shared-story entries, and saved summaries from earlier sessions.
4. **Preference memory** — communication preferences explicitly confirmed by the owner.
5. **Historical conversation recall** — relevant excerpts retrieved from messages in any earlier session belonging to the same companion.

Each saved memory records its layer, source session when available, confidence metadata, creation/update time, and retrieval count.

## Cross-session search

New user and assistant messages receive a local embedding when the optional multilingual model is installed. When a new message arrives, the backend searches earlier messages across all sessions for that companion and selects up to six relevant excerpts.

- With the local model installed, retrieval combines vector similarity and lexical overlap.
- Without the model, the system uses Persian-aware lexical matching.
- Existing messages that predate this feature can be indexed from **Memory Vault → جست‌وجوی هوشمند در مکالمات گذشته → تکمیل شاخص معنایی مکالمات قدیمی**.
- The local model must exist at `backend/models/paraphrase-multilingual-MiniLM-L12-v2`. See `docs/SEMANTIC_MEMORY.md` for installation instructions.
- If the model is installed after the backend has already started, restart the backend before checking availability or rebuilding the index.

The embedding and retrieval process is local. Chat replies may still be sent to the configured external AI provider; the local memory engine does not make the text-generation provider local.

## Duplicate and contradiction review

Before a new memory is saved, the backend compares it with existing memories using normalized Persian text, optional local vector similarity, and conservative negation/polarity checks.

Possible results:
- **Duplicate** — a very similar memory already exists.
- **Potential conflict** — the topic is similar but the statement appears to have changed direction or polarity.
- **Related** — the new fact is close to an existing fact and may need review.

These are review hints, not definitive truth judgments. Nazi AI never silently deletes or rewrites an older memory. The owner chooses to:
- replace a selected older memory with the new statement,
- save the new statement separately, or
- cancel the operation.

## Local API

- `GET /api/companions/{companion_id}/memories/index-status` — index coverage and semantic model availability.
- `POST /api/companions/{companion_id}/memories/reindex` — embed historical messages and memories that do not yet have vectors.
- `POST /api/companions/{companion_id}/memories/check` — return duplicate, related, or possible-conflict hints without writing data.
- `POST /api/companions/{companion_id}/memories` — save a memory. Conflicting or duplicate candidates require the explicit allow_conflicts confirmation flag.

## Data migration

The backend applies additive SQLite migrations at startup. Existing memories are assigned a layer based on their category, and older chat messages receive an empty embedding field until reindexed. Existing conversation text and saved memories are preserved.
