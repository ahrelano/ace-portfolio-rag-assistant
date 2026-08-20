from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.api import create_app


class RecordingChatService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[dict[str, str]]]] = []

    def respond(self, message: str, history: list[dict[str, str]]) -> str:
        self.calls.append((message, history))
        return "Ace has verified portfolio experience. Sources: Portfolio"


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RecordingChatService()
        self.client = TestClient(create_app(service_factory=lambda: self.service))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_health_is_a_safe_success_response(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_chat_accepts_a_bounded_normal_request(self) -> None:
        response = self.client.post(
            "/v1/chat",
            json={
                "message": "What projects has Ace worked on?",
                "history": [{"role": "user", "content": "Tell me about Ace."}],
            },
            headers={"Origin": "https://ace-relano-portfolio.vercel.app"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "Ace has verified portfolio experience. Sources: Portfolio")
        self.assertEqual(len(self.service.calls), 1)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "https://ace-relano-portfolio.vercel.app",
        )

    def test_chat_rejects_an_oversize_message_before_service_invocation(self) -> None:
        response = self.client.post("/v1/chat", json={"message": "x" * 501})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.service.calls, [])
