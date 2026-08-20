# Ace Relano Portfolio RAG Assistant

A small, grounded AI assistant for Ace Relano's public portfolio. It answers verified questions about approved public experience, skills, projects, and contact details.

## Key capabilities

- Answers questions about Ace's approved public portfolio.
- Retrieves relevant source material from a local Chroma index.
- Produces grounded responses with portfolio citations.
- Uses a polite, scope-limited fallback when portfolio evidence is insufficient or a request is outside scope.
- Limits each message to 500 characters.

## How it works

`Approved public Markdown → Chroma retrieval → grounded OpenAI response → portfolio citation`

The assistant is restricted to supplied portfolio evidence. It does not use web search or general world knowledge to answer questions about Ace.

## Tech stack

- Python
- LangChain and LangChain text splitters
- Chroma
- OpenAI Responses API via the OpenAI Python SDK
- `gpt-5.6-luna`
- `text-embedding-3-small`
- Gradio for local evaluation
- `python-dotenv`

## Local setup

These PowerShell commands use the repository's current scripts and dependencies.

```powershell
git clone https://github.com/ahrelano/ace-portfolio-rag-assistant.git
cd ace-portfolio-rag-assistant
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the required variable in `.env` without committing the file:

```text
OPENAI_API_KEY=<your-api-key>
```

The remaining variables in `.env.example` are optional runtime settings. Rebuild the local Chroma index, then start the local assistant:

```powershell
python -m scripts.ingest_knowledge
python -m app.gradio_app
```

Run the test suite with:

```powershell
python -m unittest discover -s tests
```

## Render deployment

This repository deploys only the FastAPI API. Gradio remains a local developer
evaluation tool and is not mounted or started by the production service.

Set these commands in a Render Python web service:

```text
Build Command: python -m pip install -r requirements.txt && python -m scripts.ingest_knowledge
Start Command: uvicorn app.api:app --host 0.0.0.0 --port $PORT
```

The build command performs the existing clean, destructive rebuild from only the
approved Markdown files in `knowledge/`. `data/chroma/` is intentionally ignored
by Git, so every Render build creates the deploy artifact's index once. API startup
only validates and opens that completed index; it never ingests, re-embeds, or
modifies Chroma. The required Render environment variable is:

```text
OPENAI_API_KEY=<your-api-key>
```

Optional bounded runtime settings are listed in `.env.example`. The API permits
browser requests only from `http://localhost:3000` and
`https://ace-relano-portfolio.vercel.app`.

## Knowledge and grounding

Only approved public portfolio Markdown files under `knowledge/` are ingested. The Markdown files are the source of truth, and the local Chroma data in `data/chroma/` is rebuilt from them with the ingestion script.

## Privacy and security

Do not commit API keys, credentials, generated Chroma data, logs, or private and company information. Keep `.env` local and use only approved public portfolio sources in the knowledge base.

## Project structure

```text
app/                    Chat, retrieval, knowledge, and local Gradio interface
knowledge/              Approved public portfolio Markdown sources
knowledge/projects/     Approved public project case studies
scripts/                Index ingestion and local inspection utilities
tests/                  Unit and RAG evaluation tests
input/portfolio.ts      Approved portfolio-source data used for validation
data/chroma/             Generated local Chroma index
.env.example            Environment variable names and defaults
requirements.txt        Python dependencies
```

## Current status

Gradio is for local testing only. The FastAPI API is ready for a Render web-service
deployment; portfolio website integration remains separate.

## Portfolio

https://ace-relano-portfolio.vercel.app
