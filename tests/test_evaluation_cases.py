from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any, Sequence

from langchain_core.documents import Document

from app.chat_service import ChatService, ChatSettings, RetrievedChunk
from tests.evaluation_cases import EVALUATION_CASES


@dataclass
class FakeResponse:
    output_text: str


class RecordingClient:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls: list[dict[str, Any]] = []
        self.responses = self

    def create(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return FakeResponse(self.answer)


class RecordingRetriever:
    def __init__(self, chunks: Sequence[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.limits: list[int] = []

    def search(
        self,
        question: str,
        *,
        limit: int,
        topics: frozenset[str] | None = None,
    ) -> Sequence[RetrievedChunk]:
        self.limits.append(limit)
        return self.chunks[:limit]

    def search_source(
        self,
        question: str,
        *,
        source_filename: str,
        limit: int,
        topics: frozenset[str] | None = None,
    ) -> Sequence[RetrievedChunk]:
        self.limits.append(limit)
        return [
            item
            for item in self.chunks
            if item.document.metadata["source_filename"] == source_filename
        ][:limit]

    def fetch_project_summaries(
        self,
        project_ids: frozenset[str],
        *,
        limit: int,
    ) -> Sequence[RetrievedChunk]:
        self.limits.append(limit)
        return [
            item
            for item in self.chunks
            if item.document.metadata.get("project_id") in project_ids
            and item.document.metadata.get("semantic_type") == "project_summary"
        ][:limit]


def evidence_chunk(
    source: str,
    section: str,
    score: float,
    content: str,
    *,
    topic: str | None = None,
    project_id: str | None = None,
    project_title: str | None = None,
) -> RetrievedChunk:
    source_url = (
        "https://ace-relano-portfolio.vercel.app/work"
        if section == "projects"
        else "https://ace-relano-portfolio.vercel.app/about"
    )
    return RetrievedChunk(
        document=Document(
            page_content=content,
            metadata={
                "source_filename": source,
                "source_url": source_url,
                "document_title": "Evaluation evidence",
                "section": section,
                "topic": topic or (
                    "profile"
                    if section == "profile"
                    else "erp"
                    if "ERP" in content or "Odoo" in content
                    else "employment"
                ),
                **(
                    {
                        "document_type": "project",
                        "project_id": project_id,
                        "project_title": project_title,
                        "semantic_type": "project_summary",
                    }
                    if project_id and project_title
                    else {}
                ),
            },
        ),
        relevance_score=score,
    )


RAG_EVIDENCE = (
    evidence_chunk(
        "knowledge/capabilities.md",
        "capabilities",
        0.73,
        "ERP systems, development, customization, design, cloud, and leadership.",
    ),
    evidence_chunk(
        "knowledge/career-timeline.md",
        "career",
        0.72,
        "Web Developer and Graphic Artist experience.",
    ),
    evidence_chunk(
        "knowledge/projects/odoo-18-commerce-platform.md",
        "projects",
        0.91,
        (
            "Odoo 18 Commerce Platform is an e-commerce and ERP project using Odoo 18 "
            "Community, Python, PostgreSQL 15, Docker, and Git/GitHub."
        ),
        topic="erp",
        project_id="odoo-18-ecommerce-erp-implementation",
        project_title="Odoo 18 Commerce Platform",
    ),
    evidence_chunk(
        "knowledge/projects/bigcommerce-acumatica-integration.md",
        "projects",
        0.90,
        (
            "BigCommerce and Acumatica Integration evaluates e-commerce and ERP APIs, "
            "webhooks, JSON, customer-class pricing, and quantity breaks."
        ),
        topic="ecommerce",
        project_id="bigcommerce-acumatica-integration",
        project_title="BigCommerce and Acumatica Integration",
    ),
    evidence_chunk(
        "knowledge/projects/acumatica-azure-staging-environment.md",
        "projects",
        0.89,
        (
            "Acumatica Azure Staging Environment uses Microsoft Azure, Acumatica 2022 R2, "
            "Windows Server, SQL Server, and IIS."
        ),
        topic="cloud",
        project_id="acumatica-azure-staging-environment",
        project_title="Acumatica Azure Staging Environment",
    ),
    evidence_chunk(
        "knowledge/profile.md",
        "profile",
        0.82,
        "Ace Relano public profile.",
    ),
)


class ReusableEvaluationCaseTests(unittest.TestCase):
    def test_route_evidence_claim_calls_and_citation_contract(self) -> None:
        for case in EVALUATION_CASES:
            with self.subTest(category=case.category, question=case.question):
                routes: list[str] = []
                retriever = RecordingRetriever(RAG_EVIDENCE)
                client = RecordingClient(case.model_answer)
                service = ChatService(
                    retriever,
                    settings=ChatSettings(),
                    api_key="test-key",
                    client_factory=lambda: client,
                    route_observer=routes.append,
                )

                response = service.respond(case.question, list(case.history))

                self.assertEqual(routes, [case.route])
                for evidence in case.required_evidence:
                    self.assertIn(evidence, response)
                for prohibited in case.prohibited_claims:
                    self.assertNotIn(prohibited, response)
                self.assertEqual(bool(retriever.limits), case.retrieval_expected)
                self.assertEqual(len(client.calls), case.model_calls)
                if case.citation_url:
                    self.assertIn(case.citation_url, response)
                else:
                    self.assertNotIn("**Read more:**", response)


if __name__ == "__main__":
    unittest.main()
