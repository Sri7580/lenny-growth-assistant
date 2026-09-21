# Agent Transcript 02 — Ingestion, Retrieval, and Test Debugging

Cloning ChatPRD/lennys-podcast-transcripts and parsing YAML frontmatter worked on the first attempt. Timestamp regex was verified against real transcript content before running full ingestion. pgvector cosine-distance search worked correctly on first run — 749 chunks across 30 episodes.

## Debugging: pytest + asyncpg "another operation is in progress"

Several tests failed with an asyncpg InterfaceError. First suspected event-loop scope and changed asyncio_default_fixture_loop_scope to session, which reduced but did not eliminate failures. Root-caused to SQLAlchemy's default connection pool handing out a pooled asyncpg connection across different event-loop contexts, since asyncpg connections are loop-bound. Fixed by switching the engine to poolclass=NullPool, trading minor performance for correctness. Result: 12/12 tests passing.

## Operational issue: local inference thermal load

Extended Ship 30/30 generations on llama3.2:3b caused real, observed laptop heat. Testing was paused and resumed after cooling rather than continuing to push the model. This informed the PRD's choice of a 3B model over larger 7B/8B alternatives.

## Verification approach

Each layer was verified independently before building the next: docker ps for infra, curl /api/health for connectivity, psql queries for ingested data, curl /api/chat for grounded generation, browser console checks for frontend errors, and cat on every file after a save step once silent save failures were discovered.

## Debugging: session reload returning empty chat (misleading CORS error)

After fixing session persistence in the frontend (localStorage + getSessionMessages), reloading a page with prior messages showed a browser console error: "blocked by CORS policy: No Access-Control-Allow-Origin header." This looked like a CORS misconfiguration, but browsers report CORS errors whenever a request fails for many underlying reasons, including server 500 errors — the actual cause was hidden behind that misleading symptom.

Checked docker logs lenny-backend directly and found the real error: fastapi.exceptions.ResponseValidationError, with 'sources' expecting a dict but receiving an empty list. Root cause: backend/app/api/chat.py initialized sources = [] (an empty list) when no retrieval sources existed, but the MessageOut Pydantic schema declared sources as dict | None, which a list can never satisfy. This caused every GET /api/sessions/{id} call for a session containing an assistant message to fail response serialization with a 500, which the browser surfaced as a CORS error since the failed response carried no CORS headers.

Fixed by changing the default to sources = None, matching the schema. Confirmed working by clearing localStorage, sending a fresh message, and reloading the page — chat history now persists correctly across reloads.

Lesson: a browser-reported CORS error is not always a CORS problem — always check the actual backend logs for the underlying exception before assuming the browser's stated error category is the real cause.
