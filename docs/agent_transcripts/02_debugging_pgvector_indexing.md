# Agent Transcript 02 — Ingestion, Retrieval, and Test Debugging

Cloning ChatPRD/lennys-podcast-transcripts and parsing YAML frontmatter worked on the first attempt. Timestamp regex was verified against real transcript content before running full ingestion. pgvector cosine-distance search worked correctly on first run — 749 chunks across 30 episodes.

## Debugging: pytest + asyncpg "another operation is in progress"

Several tests failed with an asyncpg InterfaceError. First suspected event-loop scope and changed asyncio_default_fixture_loop_scope to session, which reduced but did not eliminate failures. Root-caused to SQLAlchemy's default connection pool handing out a pooled asyncpg connection across different event-loop contexts, since asyncpg connections are loop-bound. Fixed by switching the engine to poolclass=NullPool, trading minor performance for correctness. Result: 12/12 tests passing.

## Operational issue: local inference thermal load

Extended Ship 30/30 generations on llama3.2:3b caused real, observed laptop heat. Testing was paused and resumed after cooling rather than continuing to push the model. This informed the PRD's choice of a 3B model over larger 7B/8B alternatives.

## Verification approach

Each layer was verified independently before building the next: docker ps for infra, curl /api/health for connectivity, psql queries for ingested data, curl /api/chat for grounded generation, browser console checks for frontend errors, and cat on every file after a save step once silent save failures were discovered.
