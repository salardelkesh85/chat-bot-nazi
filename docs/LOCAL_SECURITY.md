# Local Security Notes

- Development servers bind to 127.0.0.1 only.
- API keys belong in backend/.env, never in frontend source.
- .env, SQLite databases, chat messages, and memory records are ignored by Git.
- External AI providers receive prompts, selected conversation history, and relevant saved memories needed to generate a reply or memory suggestions.
- Memory suggestions are not saved without explicit owner approval.
- Do not expose the local backend port to a LAN or public network without authentication and a security review.
- Back up the local data directory securely; it contains private conversation records.
