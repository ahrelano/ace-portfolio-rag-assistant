from __future__ import annotations

import unittest

from app.chat_service import MAX_MESSAGE_CHARACTERS, MESSAGE_LENGTH_ERROR, ChatService
from app.gradio_app import validate_chat_message
from tests.test_chat_service import FakeClient, FakeRetriever, chunk


class MessageLengthTests(unittest.TestCase):
    def make_service(self) -> tuple[ChatService, FakeRetriever, FakeClient, list[str]]:
        retriever = FakeRetriever(
            [
                chunk("knowledge/profile.md"),
                chunk("knowledge/projects/odoo-18-commerce-platform.md"),
            ]
        )
        client = FakeClient()
        routes: list[str] = []
        service = ChatService(
            retriever,
            api_key="test-key",
            client_factory=lambda: client,
            route_observer=routes.append,
        )
        return service, retriever, client, routes

    @staticmethod
    def valid_question(length: int) -> str:
        question = "What has Ace worked on?"
        return question + (" " * (length - len(question)))

    def test_499_character_message_is_accepted(self) -> None:
        service, retriever, client, _ = self.make_service()

        service.respond(self.valid_question(MAX_MESSAGE_CHARACTERS - 1))

        self.assertTrue(retriever.limits)
        self.assertEqual(len(client.responses.calls), 1)

    def test_500_character_message_is_accepted(self) -> None:
        service, retriever, client, _ = self.make_service()

        service.respond(self.valid_question(MAX_MESSAGE_CHARACTERS))

        self.assertTrue(retriever.limits)
        self.assertEqual(len(client.responses.calls), 1)

    def test_501_character_message_is_rejected_before_retrieval_or_model_call(self) -> None:
        service, retriever, client, routes = self.make_service()

        response = service.respond(self.valid_question(MAX_MESSAGE_CHARACTERS + 1))

        self.assertEqual(response, MESSAGE_LENGTH_ERROR)
        self.assertEqual(retriever.limits, [])
        self.assertEqual(client.responses.calls, [])
        self.assertEqual(routes, [])

    def test_direct_manipulated_request_is_rejected_without_history_or_calls(self) -> None:
        service, retriever, client, routes = self.make_service()
        history = [{"role": "user", "content": "Earlier valid question"}]

        response = service.respond("x" * (MAX_MESSAGE_CHARACTERS + 1), history)

        self.assertEqual(response, MESSAGE_LENGTH_ERROR)
        self.assertEqual(history, [{"role": "user", "content": "Earlier valid question"}])
        self.assertEqual(retriever.limits, [])
        self.assertEqual(client.responses.calls, [])
        self.assertEqual(routes, [])

    def test_normal_short_message_keeps_existing_behavior(self) -> None:
        service, retriever, client, _ = self.make_service()

        service.respond("What has Ace worked on?")

        self.assertTrue(retriever.limits)
        self.assertEqual(len(client.responses.calls), 1)

    def test_browser_validator_accepts_the_limit_and_rejects_excess(self) -> None:
        self.assertTrue(validate_chat_message("x" * (MAX_MESSAGE_CHARACTERS - 1))["is_valid"])
        self.assertTrue(validate_chat_message("x" * MAX_MESSAGE_CHARACTERS)["is_valid"])
        validation = validate_chat_message("x" * (MAX_MESSAGE_CHARACTERS + 1))
        self.assertFalse(validation["is_valid"])
        self.assertEqual(validation["message"], MESSAGE_LENGTH_ERROR)
