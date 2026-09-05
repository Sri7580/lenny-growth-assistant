# Architecture — The Lenny Growth Assistant

## 1. System Overview

Three services, orchestrated via Docker Compose:
┌─────────────┐ HTTP/fetch ┌──────────────┐ SQLAlchemy ┌─────────────────┐
│ Frontend │ ───────────────────▶ │ Backend │ ───────────────────▶ │ PostgreSQL │
│ (Vite+React)│ ◀─── streamed text │ (FastAPI) │ ◀─── rows/vectors │ + pgvector ext │
└─────────────┘ └──────┬───────┘ └─────────────────┘
│
┌──────────┴───────────┐
▼                      ▼
┌────────────────┐ ┌─────────────────┐
│ Ollama (local) │ │Anthropic (cloud)│
│ host machine   │ |             API │
└────────────────┘ └─────────────────┘


## 2. Database Schema

| Table | Columns | Purpose |
|---|---|---|
| `sessions` | `id (UUID, PK)`, `title`, `created_at`, `updated_at` | One row per chat session |
| `messages` | `id (UUID, PK)`, `session_id (FK)`, `role`, `content`, `sources (JSON)`, `created_at` | Full conversation history, persisted per turn |
| `artifacts` | `id (UUID, PK)`, `message_id (FK)`, `artifact_type ('markdown'\|'html')`, `title`, `content`, `created_at` | Generated documents/snippets extracted from assistant responses |
| `transcript_chunks` | `id (UUID, PK)`, `guest_name`, `episode_title`, `video_id`, `youtube_url`, `publish_date`, `timestamp_ref`, `chunk_index`, `chunk_text`, `embedding (vector(384))` | RAG knowledge base, one row per ~700-word transcript chunk |

Indexing: pgvector's default index is used for cosine similarity search on
`transcript_chunks.embedding` via SQLAlchemy's `.cosine_distance()` operator.
An explicit HNSW index is a documented follow-up for scaling beyond the
current 30-episode/749-chunk corpus.

## 3. API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Reports DB, pgvector extension, and Ollama reachability independently |
| `POST` | `/api/sessions` | Creates a new chat session |
| `GET` | `/api/sessions/{id}` | Returns full message history for a session |
| `POST` | `/api/chat` | Accepts `{session_id, message, provider?}`, streams the assistant's response as plain text, persists both user and assistant messages, extracts and persists any artifact blocks |

## 4. Ingestion Flow

1. `backend/data/lennys-transcripts` is a git submodule pointing at
   `ChatPRD/lennys-podcast-transcripts`.
2. `backend/scripts/ingest.py` walks `episodes/*/transcript.md`, parses YAML
   frontmatter (guest, title, video_id, youtube_url, publish_date) via
   `python-frontmatter`.
3. Transcript body is chunked (~700 words, 100-word overlap) by simple word-count
   splitting.
4. Each chunk is scanned with a timestamp regex (`\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?`)
   to attach the nearest speaker timestamp, matching the source format
   (`Speaker Name (HH:MM:SS):`).
5. Chunks are embedded via `sentence-transformers/all-MiniLM-L6-v2` (384-dim,
   local, no external API call).
6. Chunks + vectors + metadata are inserted into `transcript_chunks`.
7. Re-running ingestion is idempotent at the episode-folder level via the
   `--limit` CLI flag; it does not currently de-duplicate on re-run
   (documented as a v2 improvement — would key on `video_id + chunk_index`).

## 5. Retrieval & Grounding Flow

1. Incoming user message is embedded with the same model used at ingestion time.
2. `retrieve_relevant_chunks()` runs a cosine-similarity query against
   `transcript_chunks`, returning the top-K (default 6) results above a
   similarity threshold (default 0.35).
3. Retrieved chunks are formatted into a context block with explicit
   `[Guest, Episode @ Timestamp]` labels and injected into the system/user
   prompt.
4. The system prompt instructs the model to answer only from provided
   context, cite sources, and explicitly state when context is insufficient.

## 6. Agent Routing

`backend/app/agent/claude_agent.py` performs simple keyword-based routing:
- If the user message contains Ship 30/30 trigger phrases (`"ship 30"`,
  `"write an essay"`, `"blog post"`, etc.), the **Ship 30/30 skill**
  (`skills/ship30_writer.py`) builds a specialized system prompt enforcing
  hook/structure/format/takeaway rules from the Ship 30 for 30 framework.
- Otherwise, the **grounded QA path** is used, with the standard citation-
  enforcing system prompt.

Both paths delegate actual token generation to whichever `BaseLLMProvider`
implementation is selected (Ollama or Anthropic), so skill logic and model
choice are fully decoupled.

## 7. Model / Provider Toggle

- `BaseLLMProvider` (abstract) defines a single `generate_response()` async
  generator method.
- `OllamaProvider` and `AnthropicProvider` implement it independently.
- Selection is controlled by `DEFAULT_LLM_PROVIDER` in `.env`, or overridden
  per-request via the `provider` field in the `/api/chat` request body (the
  frontend's model dropdown sets this per message).
- Fallback behavior: if Ollama is unreachable, the provider yields a visible
  in-chat error message (`[Error: Cannot reach Ollama. Is it running?]`)
  rather than throwing an unhandled exception; the same pattern applies to a
  missing Anthropic API key.

## 8. Artifact Generation & Security

- The model is instructed (via system prompt) to wrap standalone deliverables
  in `<artifact type="markdown|html" title="...">...</artifact>` tags.
- `skills/artifact_generator.py` extracts these blocks via regex after the
  full response is streamed, strips them from the visible chat text, and
  persists them as `Artifact` rows linked to the assistant message.
- **Frontend rendering:**
  - Markdown artifacts: rendered via a minimal in-house Markdown-to-HTML
    converter (headers, bold, bullet lists), then sanitized with DOMPurify
    before being injected via `dangerouslySetInnerHTML`.
  - HTML artifacts: rendered inside an `<iframe srcDoc={...}>` with
    `sandbox="allow-scripts"` and **no** `allow-same-origin`. This permits
    generated JavaScript to execute for interactivity, but the iframe is
    treated as an opaque-origin document: it cannot access the parent page's
    cookies, `localStorage`, or DOM, and cannot make same-origin credentialed
    requests back to our own API. Content is also passed through DOMPurify
    before reaching `srcDoc` as defense in depth.
  - **What this does not protect against:** the sandboxed iframe can still
    issue its own cross-origin `fetch`/image requests (e.g. to an
    attacker-controlled endpoint), since `sandbox="allow-scripts"` alone does
    not block network access. This residual risk is disclosed rather than
    silently accepted; a stricter mitigation (e.g. a restrictive CSP
    injected into the `srcDoc` document) is a documented follow-up.

## 9. Deployment Topology

- `docker-compose.yml` defines three services: `db` (Postgres 16 +
  pgvector), `backend` (FastAPI, hot-reload via mounted volume), `frontend`
  (Vite dev server, mounted volume).
- Ollama runs on the **host machine**, not in a container, reached from the
  backend container via `http://host.docker.internal:11434`. This was a
  deliberate simplification over containerizing Ollama, avoiding GPU
  passthrough and large image-layer complexity for a local take-home demo.
- `.env` (gitignored) holds all secrets/config; `.env.example` documents
  every variable with safe defaults.

## 10. Known Limitations (see PRD §8 for full risk discussion)

- `Message.sources` is not currently populated due to an async-generator
  architecture constraint (Python does not allow `return <value>` inside a
  generator containing `yield`). Sources are visible in-line in the answer
  text but not independently queryable via the API.
- No HNSW index yet on `transcript_chunks.embedding` — acceptable at current
  scale (749 chunks), would need addressing before ingesting the full
  ~300-episode archive.