"""Public-portfolio Markdown loading, semantic chunking, and Chroma rebuilding."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Any, Protocol, Sequence

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.source_sync import parse_approved_projects


COLLECTION_NAME = "portfolio_knowledge"
LEGACY_COLLECTION_PATTERN = re.compile(r"^portfolio_knowledge_v.*$")
# Chroma cosine distance is in [0, 2]. The chat retriever converts it to a
# bounded relevance value with ``1 - distance / 2``.
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}
REQUIRED_FRONT_MATTER = frozenset(
    {
        "source",
        "source_url",
        "section",
        "topic",
        "updated_at",
        "document_type",
        "document_id",
        "factual_topics",
    }
)
PROJECT_FRONT_MATTER = frozenset(
    {"project_id", "project_title", "project_order"}
)
REQUIRED_TOPIC_FILES = frozenset(
    {
        "knowledge/profile.md",
        "knowledge/capabilities.md",
        "knowledge/career-timeline.md",
        "knowledge/contact.md",
        "knowledge/education-and-certifications.md",
    }
)
REQUIRED_DOCUMENT_TYPES = frozenset(
    {"profile", "capabilities", "career", "contact", "education", "project"}
)
CHUNK_SIZE = 900
CHUNK_OVERLAP = 100
MIN_SUBSTANTIVE_PROJECT_LENGTH = 500
MIN_CHUNK_LENGTH = 80
REBUILD_COMMAND = "python -m scripts.ingest_knowledge"


@dataclass(frozen=True)
class KnowledgePaths:
    """Filesystem locations used by the local knowledge layer."""

    project_root: Path

    @property
    def knowledge_dir(self) -> Path:
        return self.project_root / "knowledge"

    @property
    def chroma_dir(self) -> Path:
        return self.project_root / "data" / "chroma"


@dataclass(frozen=True)
class RebuildReport:
    """Verified result of one destructive local-development index rebuild."""

    markdown_files_loaded: int
    valid_chunks_created: int
    removed_collections: tuple[str, ...]
    final_collection_name: str
    final_document_count: int
    projects_indexed: tuple[str, ...]
    persistence_path: Path
    warnings: tuple[str, ...] = ()


class Embeddings(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


def discover_markdown_sources(paths: KnowledgePaths) -> list[Path]:
    """Return only approved Markdown knowledge sources in deterministic order."""
    return sorted(paths.knowledge_dir.glob("**/*.md"))


def _parse_front_matter(raw_text: str, source_path: Path) -> tuple[dict[str, str], str]:
    normalized = raw_text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError(f"{source_path}: missing YAML front matter")

    end_marker = normalized.find("\n---\n", 4)
    if end_marker == -1:
        raise ValueError(f"{source_path}: unterminated YAML front matter")

    front_matter: dict[str, str] = {}
    for line in normalized[4:end_marker].splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"{source_path}: invalid front matter line {line!r}")
        normalized_key = key.strip()
        if normalized_key in front_matter:
            raise ValueError(f"{source_path}: duplicate front matter key {normalized_key!r}")
        front_matter[normalized_key] = value.strip().strip('"')

    missing = REQUIRED_FRONT_MATTER.difference(front_matter)
    allowed = REQUIRED_FRONT_MATTER | PROJECT_FRONT_MATTER
    unexpected = set(front_matter).difference(allowed)
    if missing or unexpected:
        raise ValueError(
            f"{source_path}: invalid front matter; missing={sorted(missing)}, "
            f"unexpected={sorted(unexpected)}"
        )
    if any(not value for value in front_matter.values()):
        raise ValueError(f"{source_path}: front matter values must not be empty")

    is_project = front_matter["document_type"] == "project"
    project_missing = PROJECT_FRONT_MATTER.difference(front_matter)
    if is_project and project_missing:
        raise ValueError(
            f"{source_path}: project front matter is missing {sorted(project_missing)}"
        )
    if not is_project and PROJECT_FRONT_MATTER.intersection(front_matter):
        raise ValueError(f"{source_path}: non-project document contains project metadata")

    content = normalized[end_marker + len("\n---\n") :].strip()
    if not content:
        raise ValueError(f"{source_path}: Markdown body must not be empty")
    return front_matter, content


def _validate_required_sources(paths: KnowledgePaths, source_paths: Sequence[Path]) -> None:
    relative_paths = {
        path.relative_to(paths.project_root).as_posix() for path in source_paths
    }
    missing = REQUIRED_TOPIC_FILES.difference(relative_paths)
    if missing:
        raise ValueError(f"Required knowledge documents are missing: {sorted(missing)}")
    if not any(path.startswith("knowledge/projects/") for path in relative_paths):
        raise ValueError("At least one approved project Markdown document is required")


def load_source_documents(paths: KnowledgePaths) -> list[Document]:
    """Load and validate every canonical portfolio Markdown source document."""
    source_paths = discover_markdown_sources(paths)
    if not source_paths:
        raise ValueError(f"No Markdown sources found under {paths.knowledge_dir}")
    _validate_required_sources(paths, source_paths)

    documents: list[Document] = []
    for source_path in source_paths:
        metadata, content = _parse_front_matter(
            source_path.read_text(encoding="utf-8"), source_path
        )
        title = next(
            (
                line.removeprefix("# ").strip()
                for line in content.splitlines()
                if line.startswith("# ")
            ),
            None,
        )
        if not title:
            raise ValueError(f"{source_path}: missing document title")
        if metadata["document_type"] == "project":
            if metadata["project_title"] != title:
                raise ValueError(
                    f"{source_path}: project_title must match the Markdown title"
                )
            if len(content) < MIN_SUBSTANTIVE_PROJECT_LENGTH:
                raise ValueError(f"{source_path}: project content is not substantive")
        documents.append(
            Document(
                page_content=content,
                metadata={
                    **metadata,
                    "source_filename": source_path.relative_to(
                        paths.project_root
                    ).as_posix(),
                    "title": title,
                    "document_title": title,
                    "url": metadata["source_url"],
                },
            )
        )

    approved_projects = parse_approved_projects(paths.project_root / "input" / "portfolio.ts")
    approved_ids = {project.slug for project in approved_projects}
    documented_ids = {
        str(document.metadata["project_id"])
        for document in documents
        if document.metadata["document_type"] == "project"
    }
    if documented_ids != approved_ids:
        raise ValueError(
            "Project Markdown must exactly match the approved portfolio project list; "
            f"missing={sorted(approved_ids - documented_ids)}, "
            f"unexpected={sorted(documented_ids - approved_ids)}"
        )
    return documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split by semantic Markdown sections, with character splitting only as fallback."""
    chunks: list[Document] = []
    seen_content: set[str] = set()

    for document in documents:
        document_type = str(document.metadata["document_type"])
        if document_type in {"profile", "career", "contact"}:
            semantic_sections = [
                (
                    "document",
                    str(document.metadata["document_title"]),
                    document.page_content,
                    {
                        "profile": "about_profile",
                        "career": "complete_career_timeline",
                        "contact": "contact",
                    }[document_type],
                )
            ]
        else:
            semantic_sections = _semantic_sections(document)

        document_chunks: list[Document] = []
        for section_key, section_title, content, semantic_type in semantic_sections:
            parts = (
                [content]
                if document_type in {"profile", "career", "contact"}
                else _split_long_semantic_section(document, content)
            )
            for part_index, part in enumerate(parts, start=1):
                normalized_content = " ".join(part.split())
                if len(normalized_content) < MIN_CHUNK_LENGTH:
                    raise ValueError(
                        f"{document.metadata['source_filename']}: nearly empty chunk "
                        f"for section {section_title!r}"
                    )
                if normalized_content in seen_content:
                    continue
                seen_content.add(normalized_content)
                part_suffix = f"-part-{part_index}" if len(parts) > 1 else ""
                document_chunks.append(
                    Document(
                        page_content=part,
                        metadata={
                            **document.metadata,
                            "semantic_type": semantic_type,
                            "section_title": section_title,
                            "chunk_key": f"{section_key}{part_suffix}",
                            "topic": _section_topic(document, section_title, semantic_type),
                        },
                    )
                )

        for index, chunk in enumerate(document_chunks):
            chunk.metadata["chunk_index"] = index
            chunk.metadata["chunk_id"] = deterministic_chunk_id(chunk)
            chunks.append(chunk)

    validate_chunks(chunks)
    return chunks


def _semantic_sections(
    document: Document,
) -> list[tuple[str, str, str, str]]:
    """Return parent-titled H2 sections in their original document order."""
    content = document.page_content
    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", content))
    title = str(document.metadata["document_title"])
    if not matches:
        return [("document", title, content, "topic_document")]

    sections: list[tuple[str, str, str, str]] = []
    for index, match in enumerate(matches):
        section_title = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        section_body = content[match.start() : end].strip()
        titled_content = f"# {title}\n\n{section_body}"
        document_type = str(document.metadata["document_type"])
        if document_type == "project":
            semantic_type = (
                "project_summary"
                if section_title.casefold() == "summary"
                else "project_section"
            )
        elif document_type == "capabilities":
            semantic_type = "capability_section"
        elif document_type == "education":
            semantic_type = "education_section"
        else:
            semantic_type = "topic_section"
        sections.append(
            (
                _slugify(section_title) or f"section-{index + 1}",
                section_title,
                titled_content,
                semantic_type,
            )
        )
    return sections


def _split_long_semantic_section(document: Document, content: str) -> list[str]:
    """Use the configured character limit only after semantic sectioning."""
    if len(content) <= CHUNK_SIZE:
        return [content]

    title_prefix = f"# {document.metadata['document_title']}\n\n"
    body = content.removeprefix(title_prefix)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max(300, CHUNK_SIZE - len(title_prefix)),
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [
        f"{title_prefix}{part}" for part in splitter.split_text(body) if part.strip()
    ]


def _section_topic(document: Document, section_title: str, semantic_type: str) -> str:
    if semantic_type == "complete_career_timeline":
        return "employment"
    if semantic_type == "contact":
        return "contact"
    if semantic_type == "about_profile":
        return "profile"
    heading = section_title.casefold()
    if document.metadata["document_type"] == "capabilities":
        if "e-commerce" in heading:
            return "ecommerce"
        if "erp" in heading or "integration" in heading:
            return "erp"
        if "ai" in heading or "data analysis" in heading:
            return "ai"
        if "cloud" in heading:
            return "cloud"
        if "graphic" in heading or "photo" in heading:
            return "graphic_design"
        if "customer service" in heading:
            return "non_development_capabilities"
        return "software_development"
    return str(document.metadata["topic"])


def _slugify(value: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", value.casefold()))


def deterministic_chunk_id(chunk: Document) -> str:
    """Return an ID stable for a document and semantic section across rebuilds."""
    document_id = str(chunk.metadata["document_id"])
    chunk_key = str(chunk.metadata["chunk_key"])
    return sha256(f"{document_id}:{chunk_key}".encode("utf-8")).hexdigest()


def validate_chunks(chunks: list[Document]) -> None:
    """Validate content, deterministic IDs, metadata, and required index coverage."""
    if not chunks:
        raise ValueError("No valid chunks were produced")
    required_metadata = REQUIRED_FRONT_MATTER | {
        "source_filename",
        "title",
        "document_title",
        "url",
        "semantic_type",
        "section_title",
        "chunk_key",
        "chunk_index",
        "chunk_id",
    }
    deterministic_ids: list[str] = []
    for chunk in chunks:
        missing = required_metadata.difference(chunk.metadata)
        if missing:
            raise ValueError(f"Chunk missing metadata: {sorted(missing)}")
        if not chunk.page_content.strip():
            raise ValueError("Chunk content must not be empty")
        expected_id = deterministic_chunk_id(chunk)
        if chunk.metadata["chunk_id"] != expected_id:
            raise ValueError("Chunk metadata contains a non-deterministic ID")
        deterministic_ids.append(expected_id)
        if chunk.metadata["document_type"] == "project":
            project_missing = PROJECT_FRONT_MATTER.difference(chunk.metadata)
            if project_missing:
                raise ValueError(f"Project chunk missing metadata: {sorted(project_missing)}")

    if len(deterministic_ids) != len(set(deterministic_ids)):
        raise ValueError("Duplicate deterministic chunk IDs were produced")
    document_types = {str(chunk.metadata["document_type"]) for chunk in chunks}
    missing_types = REQUIRED_DOCUMENT_TYPES.difference(document_types)
    if missing_types:
        raise ValueError(f"Required document types are missing: {sorted(missing_types)}")

    project_ids = {
        str(chunk.metadata["project_id"])
        for chunk in chunks
        if chunk.metadata["document_type"] == "project"
    }
    projects_with_chunks = {
        str(chunk.metadata["project_id"])
        for chunk in chunks
        if chunk.metadata["document_type"] == "project" and chunk.page_content.strip()
    }
    if projects_with_chunks != project_ids:
        raise ValueError("Every approved project must produce at least one valid chunk")


def build_chunks(paths: KnowledgePaths) -> list[Document]:
    """Load, semantically split, deduplicate, and validate approved Markdown."""
    return chunk_documents(load_source_documents(paths))


def application_collection_names(client: Any) -> tuple[str, ...]:
    """Return only stable or legacy collections owned by this application."""
    names = tuple(collection.name for collection in client.list_collections())
    return tuple(
        sorted(
            name
            for name in names
            if name == COLLECTION_NAME or LEGACY_COLLECTION_PATTERN.fullmatch(name)
        )
    )


def rebuild_index(
    paths: KnowledgePaths,
    chunks: list[Document],
    *,
    embeddings: Embeddings | None = None,
    client: Any | None = None,
) -> RebuildReport:
    """Delete only app collections and rebuild one verified stable collection.

    This intentionally destructive approach is for the current local-development phase.
    A staged or atomic collection replacement should be considered before production use.
    """
    validate_chunks(chunks)
    ids = [deterministic_chunk_id(chunk) for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate deterministic IDs prevent a safe rebuild")

    if client is None:
        import chromadb

        paths.chroma_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(paths.chroma_dir))
    if embeddings is None:
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    removed_collections = application_collection_names(client)
    for collection_name in removed_collections:
        client.delete_collection(collection_name)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata=CHROMA_COLLECTION_METADATA,
    )
    try:
        vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
        if len(vectors) != len(chunks) or any(not vector for vector in vectors):
            raise RuntimeError("Embedding output did not match the validated chunk count")
        metadatas = [_chroma_metadata(chunk.metadata) for chunk in chunks]
        for start in range(0, len(chunks), 100):
            end = start + 100
            collection.add(
                ids=ids[start:end],
                documents=[chunk.page_content for chunk in chunks[start:end]],
                metadatas=metadatas[start:end],
                embeddings=vectors[start:end],
            )
    except Exception as exc:
        raise RuntimeError(
            "Portfolio index rebuild is incomplete after the previous application "
            "collection was removed"
        ) from exc

    final_count = collection.count()
    if final_count != len(chunks):
        raise RuntimeError(
            "Portfolio index rebuild is incomplete: inserted count does not match "
            f"the expected chunk count ({final_count} != {len(chunks)})"
        )
    _verify_rebuilt_collection(client, collection, chunks)
    project_titles = tuple(
        dict.fromkeys(
            str(chunk.metadata["project_title"])
            for chunk in chunks
            if chunk.metadata["document_type"] == "project"
        )
    )
    return RebuildReport(
        markdown_files_loaded=len(
            {str(chunk.metadata["source_filename"]) for chunk in chunks}
        ),
        valid_chunks_created=len(chunks),
        removed_collections=removed_collections,
        final_collection_name=COLLECTION_NAME,
        final_document_count=final_count,
        projects_indexed=project_titles,
        persistence_path=paths.chroma_dir.resolve(),
        warnings=(
            "Destructive rebuild mode is intended for local development; use a staged "
            "or atomic replacement strategy before production deployment.",
        ),
    )


def ingest_chunks(
    paths: KnowledgePaths,
    chunks: list[Document],
    *,
    embeddings: Embeddings | None = None,
    client: Any | None = None,
) -> RebuildReport:
    """Compatibility entry point: normal ingestion is always a clean full rebuild."""
    return rebuild_index(paths, chunks, embeddings=embeddings, client=client)


def _chroma_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    allowed_types = (str, int, float, bool)
    return {
        str(key): value if isinstance(value, allowed_types) else str(value)
        for key, value in metadata.items()
    }


def _verify_rebuilt_collection(client: Any, collection: Any, chunks: list[Document]) -> None:
    names = tuple(item.name for item in client.list_collections())
    application_names = tuple(
        name
        for name in names
        if name == COLLECTION_NAME or LEGACY_COLLECTION_PATTERN.fullmatch(name)
    )
    if application_names != (COLLECTION_NAME,):
        raise RuntimeError(
            f"Expected exactly one application collection, found {sorted(application_names)}"
        )
    stored = collection.get(include=["metadatas"])
    metadatas = [metadata or {} for metadata in stored.get("metadatas", [])]
    stored_types = {str(metadata.get("document_type", "")) for metadata in metadatas}
    missing_types = REQUIRED_DOCUMENT_TYPES.difference(stored_types)
    if missing_types:
        raise RuntimeError(f"Rebuilt collection is missing document types: {sorted(missing_types)}")
    expected_projects = {
        str(chunk.metadata["project_id"])
        for chunk in chunks
        if chunk.metadata["document_type"] == "project"
    }
    stored_projects = {
        str(metadata.get("project_id"))
        for metadata in metadatas
        if metadata.get("document_type") == "project"
    }
    if stored_projects != expected_projects:
        raise RuntimeError(
            "Rebuilt collection does not contain every approved project; "
            f"missing={sorted(expected_projects - stored_projects)}"
        )


def validate_existing_index(paths: KnowledgePaths, *, client: Any | None = None) -> int:
    """Fail without creating a collection when the stable index is absent or empty."""
    if client is None:
        if not paths.chroma_dir.exists():
            raise RuntimeError(
                f"Portfolio knowledge index has not been built. Run: {REBUILD_COMMAND}"
            )
        import chromadb

        client = chromadb.PersistentClient(path=str(paths.chroma_dir))
    collection_names = {item.name for item in client.list_collections()}
    if COLLECTION_NAME not in collection_names:
        raise RuntimeError(
            f"Portfolio knowledge collection {COLLECTION_NAME!r} does not exist. "
            f"Run: {REBUILD_COMMAND}"
        )
    collection = client.get_collection(COLLECTION_NAME)
    count = collection.count()
    if count <= 0:
        raise RuntimeError(
            f"Portfolio knowledge collection {COLLECTION_NAME!r} is empty. "
            f"Run: {REBUILD_COMMAND}"
        )
    return count


def similarity_search_smoke_test(paths: KnowledgePaths, query: str) -> list[Document]:
    """Query the existing stable index and ensure citation metadata is retained."""
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings

    validate_existing_index(paths)
    store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(paths.chroma_dir),
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
        collection_metadata=CHROMA_COLLECTION_METADATA,
    )
    results = store.similarity_search(query, k=3)
    if not results:
        raise RuntimeError("Chroma similarity search returned no chunks")
    return results
