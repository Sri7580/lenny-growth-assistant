# Agent Transcript 01 — Initial Scaffolding

Scaffolded the full project: folder structure, Docker Compose, FastAPI skeleton, ingestion pipeline, RAG retriever, LLM providers, agent orchestration, Ship 30/30 skill, artifact extraction, sessions/chat API, and React frontend.

## Failed attempts and corrections

1. Truncated filename from a bulk touch command produced test_providers.pytouch instead of a clean .py file. Caught via ls, removed with git rm.
2. SyntaxError: 'return' with value in async generator — run_agent_turn() used yield to stream tokens but also tried to return a tuple at the end, which Python disallows. Crashed the backend on startup. Fixed by removing the return and documenting the resulting limitation (sources not persisted) in architecture.md.
3. Tailwind v3 config assumptions didn't apply — project used Tailwind v4's Vite-plugin approach instead of PostCSS config. Diagnosed by noting tailwind.config.js didn't exist (expected in v4) and confirmed via a visual smoke test before building real UI.
4. Local model (llama3.2:3b) does not reliably follow the artifact-wrapper instruction or hit the target word count for Ship 30/30 essays, verified directly via curl. Documented as a genuine local-model trade-off rather than papered over.
5. Several doc files silently failed to save via an editor-paste workflow and were later found empty when verified with cat. Fixed by verifying every file's actual on-disk content immediately after saving, rather than trusting the save step alone.
