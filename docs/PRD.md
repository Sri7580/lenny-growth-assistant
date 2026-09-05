# PRD — The Lenny Growth Assistant

## 1. Overview

The Lenny Growth Assistant is an internal conversational tool that lets product and growth professionals query Lenny's Podcast transcript archive in natural language, receive source-grounded answers, and convert those answers into polished, shareable content without needing to understand the underlying AI infrastructure.

## 2. User & Problem

**Primary persona:** A Growth PM who wants tactical, expert-sourced advice on product/growth questions but does not have time to listen to 200+ hours of podcast audio.

**Job to be done:** Get a fast, trustworthy, cited answer drawn from real practitioner interviews, without manually searching transcripts.

## 3. Success Metrics

- Retrieval groundedness: >=90% of answers include a real citation
- Local inference time-to-first-token: < 4s
- Artifact render safety: 0 XSS vulnerabilities
- Session continuity: 100% survive a page reload

## 4. Assumptions

- Ingested a curated 30-episode subset, not the full ~300-episode archive, to keep embedding time and demo latency reasonable.
- Used the ChatPRD/lennys-podcast-transcripts GitHub archive rather than a custom scraper.
- Used sentence-transformers/all-MiniLM-L6-v2 for embeddings, runs locally with no external API dependency.
- No authentication or multi-tenancy for this assessment.
- No real-time transcript refresh; ingestion is a manual re-runnable script.
- Used llama3.2:3b instead of larger 7B/8B models, chosen for feasibility on standard laptop hardware.

## 5. Scope

In scope: grounded Q&A, session persistence, local/cloud provider toggle, Ship 30/30 skill, artifact viewer, health checks, Docker Compose startup.

Out of scope: multi-user auth, real-time ingestion pipeline, full transcript corpus, rate limiting, persisted retrieval source metadata.

## 6. Core User Flows

1. New session, grounded question, cited streamed answer.
2. Follow-up questions use conversation history.
3. Ship 30/30 requests trigger a dedicated essay-writing skill.
4. Artifact blocks render in the right-hand viewer pane.
5. Provider dropdown switches between local and cloud models per message.
6. Sessions persist across page reloads via localStorage.

## 7. Acceptance Criteria

- Session created and persists across reloads
- Answers cite real guest/episode names when context exists
- Out-of-domain questions get an explicit insufficient-information response
- Provider dropdown changes which LLM is used
- Health check reports DB, vector index, and Ollama status
- HTML artifacts render in a sandboxed iframe without allow-same-origin
- docker compose up brings up the full stack with only .env required

## 8. Risks & Trade-offs

- Local model (llama3.2:3b) reliably produces grounded content but consistently fails to follow the artifact-wrapper instruction, and undershoots the 1,250-word Ship 30/30 target (observed ~550-650 words). This is a genuine small-model limitation, not a skill-logic bug.
- Hallucination risk is mitigated by prompt-level grounding instructions, not a hard guarantee.
- Local CPU inference caused real, observed thermal load during extended generations.
- Transcript data comes from a third-party community archive of Lenny's own public transcripts; redistribution terms would need confirming for production use.
- Artifact sandboxing (allow-scripts without allow-same-origin, plus DOMPurify) blocks cookie/DOM/localStorage access but does not block outbound network requests from the iframe.
- Retrieval source metadata isn't persisted to Message.sources due to an async-generator limitation (Python disallows return-with-value in a generator that yields).

## 9. Implementation Plan

Infra, ingestion, retrieval, providers, agent/skills, API, frontend, hardening, docs and tests, demo video — executed in that order.
