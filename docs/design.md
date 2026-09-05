# Design — The Lenny Growth Assistant

## 1. UI/UX Principles

- **Two-pane workspace, not a linear chat.** Chat and generated artifacts are
  first-class, simultaneous outputs — mirroring the Claude Artifacts pattern
  the assignment explicitly asks for. The user should never lose the chat
  thread to view a generated document.
- **Transparency over polish.** The model/provider in use is always visible
  (dropdown badge, top-right of chat pane) rather than hidden behind settings,
  since knowing whether an answer came from a local or cloud model materially
  affects how much the user should trust it.
- **Fail visibly, not silently.** Errors (Ollama unreachable, missing API key,
  out-of-domain question) are surfaced as inline chat/error content, never a
  blank screen or a swallowed exception.
- **Minimal chrome.** No sidebar navigation, no settings modal, no onboarding
  flow — this is a focused internal tool, not a consumer product, and scope
  was deliberately kept to what supports the core Q&A + artifact workflow.

## 2. Information Architecture

App
├── Left pane (50% width) — Chat
│ ├── Header: title + model/provider selector
│ ├── Message list (scrollable, auto-scrolls to newest)
│ ├── Inline error banner (if present)
│ └── Input bar: text field + send button
└── Right pane (50% width) — Artifact Viewer
├── Empty state: placeholder copy
└── Populated state:
├── Header: artifact type badge + title + close button
└── Rendered content (Markdown or sandboxed HTML iframe)


Single source of truth for conversation state lives in `useChatStream`
(messages, streaming status, error); `App.tsx` owns session identity and
artifact-detection, keeping components themselves presentational.

## 3. Key Interaction States

| State | Behavior |
|---|---|
| Initial load | Session auto-created (or restored from `localStorage`); empty-state copy shown in both panes |
| User sends message | User bubble appears immediately; assistant bubble appears empty with "thinking…" placeholder |
| Streaming | Assistant bubble content updates token-by-token as text arrives |
| Artifact detected | Right pane transitions from empty state to rendered content the moment an `<artifact>` block is parsed out of the streamed response |
| Provider switch | Dropdown change only affects the *next* message; does not retroactively alter prior messages |
| Error (Ollama down, bad request, etc.) | Red inline banner in the chat pane; does not crash the UI or lose prior conversation |
| Page reload | Session ID read from `localStorage`; full history re-fetched from `/api/sessions/{id}` and re-rendered |
| New chat | Explicit button creates a fresh session, clears local message list and artifact pane |

## 4. Responsive Behavior

Current implementation targets desktop/laptop usage (the primary persona's
context — a PM at their desk). The two-pane 50/50 split is fixed-width in the
current build.

**Documented, not yet implemented:** on narrow viewports the layout should
collapse to a single column with the artifact pane becoming a slide-over/tab
rather than a persistent side panel, since a 50/50 split becomes unusable
below ~768px. This is scoped out for the assessment timeline but flagged
explicitly here rather than silently ignored, per the assignment's request
for documented scope decisions.

## 5. Accessibility Considerations

- Semantic HTML used for structure (`<form>`, `<button>`, `<input>`) rather
  than div-based fake controls, so keyboard navigation and screen readers get
  reasonable default behavior.
- The iframe used for HTML artifacts has a `title` attribute
  (`"artifact-preview"`) for screen-reader context.
- **Known gaps, disclosed rather than hidden:** no live-region announcement
  for streaming message updates (a screen reader user would not be notified
  token-by-token that new content is arriving), and no focus management when
  the artifact pane populates. Both are reasonable v2 additions given more
  time; flagged here as an honest scope limitation rather than an oversight
  discovered later.

## 6. Visual Design Decisions

- **Neutral palette (slate/white/black)** rather than a branded color scheme,
  since this is an internal tool where legibility and a "serious工具" feel
  matter more than brand identity.
- **Chat bubbles differentiate by fill, not just alignment** (dark filled for
  user, light gray for assistant) so color-blind users aren't relying solely
  on left/right position to distinguish speakers.
- **Artifact type shown as a small uppercase label** (MARKDOWN / HTML) above
  the title, so the user always knows what kind of content they're looking at
  and, implicitly, how it's being rendered/sandboxed.