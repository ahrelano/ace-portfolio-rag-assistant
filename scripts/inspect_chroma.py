"""List Chroma collections and the stable portfolio index's project metadata."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge import COLLECTION_NAME, KnowledgePaths  # noqa: E402


def main() -> int:
    import chromadb

    paths = KnowledgePaths(PROJECT_ROOT)
    if not paths.chroma_dir.exists():
        print(f"No Chroma persistence directory exists at {paths.chroma_dir.resolve()}.")
        return 1
    client = chromadb.PersistentClient(path=str(paths.chroma_dir))
    collections = sorted(client.list_collections(), key=lambda item: item.name)
    if not collections:
        print("No Chroma collections found.")
        return 0

    print("Collections:")
    for collection in collections:
        print(f"- {collection.name}: {collection.count()} records")

    names = {collection.name for collection in collections}
    if COLLECTION_NAME not in names:
        print(f"Stable collection {COLLECTION_NAME!r} is not present.")
        return 0

    stable = client.get_collection(COLLECTION_NAME)
    result = stable.get(
        where={"document_type": "project"},
        include=["metadatas"],
    )
    project_rows = sorted(
        {
            (
                str(metadata.get("project_order", "")),
                str(metadata.get("project_title", "")),
                str(metadata.get("project_id", "")),
                str(metadata.get("document_id", "")),
            )
            for metadata in (result.get("metadatas") or [])
            if metadata
        }
    )
    print("Indexed projects:")
    if not project_rows:
        print("- none (the stable collection may predate project metadata)")
    for _, title, project_id, document_id in project_rows:
        print(
            f"- title={title or 'unknown'} project_id={project_id or 'unknown'} "
            f"document_id={document_id or 'unknown'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
