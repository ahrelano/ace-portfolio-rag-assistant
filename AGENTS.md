# AGENTS.md — Portfolio RAG Assistant

## Purpose

Build a public-safe RAG API for Ace Relano's portfolio. It is a separate Python project that will later be called by the existing `Ace Relano - Portfolio` Next.js site.

## Scope

- Answer verified questions about the public portfolio with source citations.
- Keep the assistant visibly identified as AI; it must not impersonate Ace or claim personal knowledge beyond approved sources.
- Keep Version 1 simple: retrieve → grounded answer → citations → optional private audit event.
- No general chat, autonomous agents, browser access, file uploads, user accounts, or persistent conversation database.

## Intended Layout

```text
app/                 FastAPI routes, schemas, services
knowledge/           approved source documents and metadata
scripts/             ingestion and local utility scripts
tests/               unit, API, and RAG-evaluation tests
data/chroma/         generated local vector-store data; never hand-edit
.env.example         variable names only; no values or secrets
```

Adapt this layout only when the actual project structure makes a change clearly better.

## Engineering Rules

- Use Python 3.12, type hints, Pydantic request/response models, and small testable functions.
- Default stack: FastAPI, LangChain, Chroma, OpenAI Responses API, `gpt-5.6-luna`, and `text-embedding-3-small`.
- Keep retrieval configuration centralized. Include `source`, `title`, `url`, `section`, and `updated_at` metadata for every chunk.
- The API key and Google credentials are server-only environment variables. Never prefix them for frontend exposure or commit them.
- Every unsupported, weak-retrieval, or sensitive request must receive a polite scope-limited answer rather than a guess.
- Keep model context, output length, and request count bounded. One normal chat message should need one generation call.

## Quality Gate

Before calling a change ready:

1. Run relevant unit/API tests.
2. Run the ingestion or retrieval smoke test when knowledge/retrieval changes.
3. Check the evaluation fixture for correct grounded answers, citations, unsupported questions, and prompt-injection resistance.
4. Confirm no secrets, private sources, or raw visitor messages entered the repository.

## Interfaces

Use versioned, typed HTTP contracts. The intended first endpoints are:

- `GET /health`
- `POST /v1/chat`
- `POST /v1/feedback` only when feedback is implemented

The browser calls the chat API; it never calls OpenAI, Google Sheets, or n8n directly. Logging must be non-blocking from the visitor's perspective. Design the audit event as a replaceable sink so Google Sheets can later be replaced or supplemented by a secure n8n webhook.

## Gradio

Gradio is for local developer evaluation of chat answers, retrieved chunks, and citations. It is not the public portfolio interface and must not be exposed by default in production.

## Change Discipline

- Inspect before editing; make the smallest relevant change.
- Do not commit, push, deploy, enable external logging, or create paid cloud resources without explicit user approval.
- Do not enter repeated plan cycles. After an approved plan, implement and validate.
- Report changed files and actual test results. If a test cannot run, state why and provide the exact manual check.
