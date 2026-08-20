from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import chromadb
from langchain_chroma import Chroma

from app.chat_service import ChromaPortfolioRetriever
from app.knowledge import (
    COLLECTION_NAME,
    REQUIRED_DOCUMENT_TYPES,
    REQUIRED_FRONT_MATTER,
    KnowledgePaths,
    application_collection_names,
    build_chunks,
    deterministic_chunk_id,
    discover_markdown_sources,
    load_source_documents,
    rebuild_index,
    validate_existing_index,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PATHS = KnowledgePaths(PROJECT_ROOT)


class FakeEmbeddings:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.fail:
            raise RuntimeError("synthetic embedding failure")
        return [
            [float((index % 7) + 1), float((len(text) % 11) + 1), 1.0]
            for index, text in enumerate(texts)
        ]


class KeywordEmbeddings:
    @staticmethod
    def _vector(text: str) -> list[float]:
        normalized = text.casefold()
        return [
            float("odoo" in normalized),
            float("contact" in normalized or "email" in normalized),
            float("racetronix" in normalized or "career" in normalized),
            1.0,
        ]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


def empty_chroma_client():
    client = chromadb.EphemeralClient()
    for collection in client.list_collections():
        client.delete_collection(collection.name)
    return client


class KnowledgeIngestionTests(unittest.TestCase):
    def test_discovers_the_eight_canonical_markdown_sources(self) -> None:
        sources = discover_markdown_sources(PATHS)
        self.assertEqual(len(sources), 8)
        self.assertEqual(
            {source.name for source in sources if source.parent == PATHS.knowledge_dir},
            {
                "profile.md",
                "capabilities.md",
                "career-timeline.md",
                "contact.md",
                "education-and-certifications.md",
            },
        )
        self.assertEqual(len([source for source in sources if source.parent.name == "projects"]), 3)

    def test_source_documents_have_canonical_metadata_and_approved_projects(self) -> None:
        documents = load_source_documents(PATHS)
        self.assertEqual(
            {str(document.metadata["document_type"]) for document in documents},
            REQUIRED_DOCUMENT_TYPES,
        )
        for document in documents:
            self.assertTrue(REQUIRED_FRONT_MATTER.issubset(document.metadata))
            for key in (
                "source_filename",
                "title",
                "document_title",
                "url",
                "document_id",
            ):
                self.assertTrue(document.metadata[key])
            self.assertEqual(document.metadata["url"], document.metadata["source_url"])

        projects = [
            document for document in documents if document.metadata["document_type"] == "project"
        ]
        self.assertEqual(len(projects), 3)
        for project in projects:
            self.assertEqual(project.metadata["project_title"], project.metadata["title"])
            self.assertIn("/work/", project.metadata["source_url"])
            self.assertGreater(len(project.page_content), 500)

    def test_chunk_ids_are_deterministic_unique_and_version_free(self) -> None:
        first_run = build_chunks(PATHS)
        second_run = build_chunks(PATHS)
        first_ids = [deterministic_chunk_id(chunk) for chunk in first_run]
        second_ids = [deterministic_chunk_id(chunk) for chunk in second_run]
        self.assertEqual(first_ids, second_ids)
        self.assertEqual(len(first_ids), len(set(first_ids)))
        for chunk in first_run:
            self.assertEqual(chunk.metadata["chunk_id"], deterministic_chunk_id(chunk))
            self.assertNotIn("index_version", chunk.metadata)
            self.assertIn("semantic_type", chunk.metadata)
            self.assertIn("section_title", chunk.metadata)

    def test_contact_and_complete_career_timeline_remain_intact(self) -> None:
        chunks = build_chunks(PATHS)
        contact = [chunk for chunk in chunks if chunk.metadata["document_type"] == "contact"]
        career = [chunk for chunk in chunks if chunk.metadata["document_type"] == "career"]
        self.assertEqual(len(contact), 1)
        self.assertEqual(len(career), 1)
        self.assertIn("relano.aceheart@gmail.com", contact[0].page_content)
        self.assertIn("linkedin.com", contact[0].page_content)
        self.assertIn("github.com", contact[0].page_content)

        timeline = career[0].page_content
        expected_roles = (
            "1. Associate Software Engineer Trainee",
            "2. Customer Service Representative",
            "3. Graphic Artist — Office Beacon Philippines Inc",
            "4. Graphic Artist — CV Services Group (Shore 360)",
            "5. Web Developer — Racetronix",
        )
        positions = [timeline.index(role) for role in expected_roles]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("earliest portfolio-listed job", timeline)
        self.assertIn("not establish whether it was Ace's absolute first-ever job", timeline)

    def test_projects_are_heading_split_with_titles_urls_and_summary_chunks(self) -> None:
        project_chunks = [
            chunk for chunk in build_chunks(PATHS) if chunk.metadata["document_type"] == "project"
        ]
        project_ids = {str(chunk.metadata["project_id"]) for chunk in project_chunks}
        self.assertEqual(
            project_ids,
            {
                "odoo-18-ecommerce-erp-implementation",
                "bigcommerce-acumatica-integration",
                "acumatica-azure-staging-environment",
            },
        )
        for project_id in project_ids:
            chunks = [
                chunk for chunk in project_chunks if chunk.metadata["project_id"] == project_id
            ]
            self.assertTrue(any(chunk.metadata["semantic_type"] == "project_summary" for chunk in chunks))
            for chunk in chunks:
                self.assertTrue(chunk.page_content.startswith(f"# {chunk.metadata['project_title']}"))
                self.assertEqual(chunk.metadata["source_url"], chunk.metadata["url"])

    def test_clean_rebuild_removes_only_app_collections_and_is_idempotent(self) -> None:
        chunks = build_chunks(PATHS)
        client = empty_chroma_client()
        for name in (
            COLLECTION_NAME,
            "portfolio_knowledge_v1",
            "portfolio_knowledge_v2",
            "portfolio_knowledge_v99-test",
            "unrelated_collection",
        ):
            client.create_collection(name)

        embeddings = FakeEmbeddings()
        first = rebuild_index(PATHS, chunks, embeddings=embeddings, client=client)
        self.assertEqual(application_collection_names(client), (COLLECTION_NAME,))
        self.assertIn("unrelated_collection", {item.name for item in client.list_collections()})
        self.assertEqual(first.final_document_count, len(chunks))
        self.assertEqual(len(first.projects_indexed), 3)

        second = rebuild_index(PATHS, chunks, embeddings=embeddings, client=client)
        self.assertEqual(second.final_document_count, len(chunks))
        self.assertEqual(client.get_collection(COLLECTION_NAME).count(), len(chunks))
        self.assertEqual(embeddings.calls, 2)

    def test_fake_embedding_rebuild_supports_project_and_contact_retrieval(self) -> None:
        client = empty_chroma_client()
        embeddings = KeywordEmbeddings()
        rebuild_index(PATHS, build_chunks(PATHS), embeddings=embeddings, client=client)
        store = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )

        project = store.similarity_search(
            "Odoo 18 project",
            k=1,
            filter={"project_id": "odoo-18-ecommerce-erp-implementation"},
        )[0]
        contact_rows = store.get(
            where={"document_type": "contact"},
            include=["documents", "metadatas"],
        )
        project_summaries = store.get(
            where={
                "$and": [
                    {
                        "project_id": {
                            "$in": [
                                "odoo-18-ecommerce-erp-implementation",
                                "bigcommerce-acumatica-integration",
                            ]
                        }
                    },
                    {"semantic_type": "project_summary"},
                ]
            },
            include=["metadatas"],
        )

        self.assertEqual(project.metadata["project_title"], "Odoo 18 Commerce Platform")
        self.assertIn("/work/odoo-18-ecommerce-erp-implementation", project.metadata["source_url"])
        self.assertEqual(len(contact_rows["documents"]), 1)
        self.assertIn("relano.aceheart@gmail.com", contact_rows["documents"][0])
        self.assertEqual(len(project_summaries["metadatas"]), 2)

    def test_invalid_chunks_prevent_collection_deletion(self) -> None:
        client = empty_chroma_client()
        client.create_collection("portfolio_knowledge_v2")
        client.create_collection("unrelated_collection")
        with self.assertRaisesRegex(ValueError, "No valid chunks"):
            rebuild_index(PATHS, [], embeddings=FakeEmbeddings(), client=client)
        self.assertEqual(
            {item.name for item in client.list_collections()},
            {"portfolio_knowledge_v2", "unrelated_collection"},
        )

    def test_empty_markdown_fails_before_the_rebuild_can_delete_collections(self) -> None:
        client = empty_chroma_client()
        client.create_collection("portfolio_knowledge_v2")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            shutil.copytree(PROJECT_ROOT / "knowledge", temp_root / "knowledge")
            shutil.copytree(PROJECT_ROOT / "input", temp_root / "input")
            (temp_root / "knowledge" / "profile.md").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing YAML front matter"):
                invalid_chunks = build_chunks(KnowledgePaths(temp_root))
                rebuild_index(
                    KnowledgePaths(temp_root),
                    invalid_chunks,
                    embeddings=FakeEmbeddings(),
                    client=client,
                )
        self.assertEqual(
            {item.name for item in client.list_collections()},
            {"portfolio_knowledge_v2"},
        )

    def test_embedding_failure_is_reported_as_incomplete(self) -> None:
        chunks = build_chunks(PATHS)
        client = empty_chroma_client()
        client.create_collection("portfolio_knowledge_v1")
        with self.assertRaisesRegex(RuntimeError, "rebuild is incomplete"):
            rebuild_index(
                PATHS,
                chunks,
                embeddings=FakeEmbeddings(fail=True),
                client=client,
            )
        self.assertEqual(application_collection_names(client), (COLLECTION_NAME,))
        self.assertEqual(client.get_collection(COLLECTION_NAME).count(), 0)

    def test_runtime_validation_rejects_missing_or_empty_stable_collection(self) -> None:
        client = empty_chroma_client()
        client.create_collection("portfolio_knowledge_v2")
        with self.assertRaisesRegex(RuntimeError, "python -m scripts.ingest_knowledge"):
            validate_existing_index(PATHS, client=client)
        client.create_collection(COLLECTION_NAME)
        with self.assertRaisesRegex(RuntimeError, "empty"):
            validate_existing_index(PATHS, client=client)

    def test_chat_retriever_does_not_create_or_rebuild_a_missing_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            with self.assertRaisesRegex(RuntimeError, "python -m scripts.ingest_knowledge"):
                ChromaPortfolioRetriever(temp_root)
            self.assertFalse((temp_root / "data" / "chroma").exists())


if __name__ == "__main__":
    unittest.main()
