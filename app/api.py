"""Production FastAPI surface for the public portfolio RAG assistant."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.chat_service import (
    ChromaPortfolioRetriever,
    ChatService,
    MAX_MESSAGE_CHARACTERS,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ORIGINS = (
    "http://localhost:3000",
    "https://ace-relano-portfolio.vercel.app",
)
ChatServiceFactory = Callable[[], ChatService]


class ChatHistoryMessage(BaseModel):
    """A bounded, non-persistent browser conversation item."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARACTERS)


class ChatRequest(BaseModel):
    """Versioned public chat request."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARACTERS)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=8)


class ChatResponse(BaseModel):
    """Grounded answer, including the service's source-citation footer when applicable."""

    answer: str


def _create_chat_service() -> ChatService:
    """Open an already-built index; never ingest or modify it at API runtime."""
    return ChatService(ChromaPortfolioRetriever(PROJECT_ROOT))


def create_app(service_factory: ChatServiceFactory = _create_chat_service) -> FastAPI:
    """Create the API without exposing the local Gradio evaluation interface."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Local development may use .env; Render injects the same values directly.
        load_dotenv(PROJECT_ROOT / ".env")
        # The retriever validates the persistent index and opens it read-only. It
        # deliberately does not invoke the ingestion script or create embeddings.
        app.state.chat_service = service_factory()
        yield

    app = FastAPI(title="Ace Relano Portfolio RAG API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(ALLOWED_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(payload: ChatRequest, request: Request) -> ChatResponse:
        history: Sequence[dict[str, str]] = [item.model_dump() for item in payload.history]
        answer = request.app.state.chat_service.respond(payload.message, history)
        return ChatResponse(answer=answer)

    return app


app = create_app()
