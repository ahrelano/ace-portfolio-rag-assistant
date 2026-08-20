"""Validate all Markdown, then replace every portfolio app collection with one stable index."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge import (  # noqa: E402
    COLLECTION_NAME,
    KnowledgePaths,
    build_chunks,
    discover_markdown_sources,
    rebuild_index,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "WARNING: without --dry-run this command deletes the current portfolio_knowledge "
            "and portfolio_knowledge_v* collections before rebuilding portfolio_knowledge."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate sources, metadata, IDs, and chunking without OpenAI or Chroma changes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    paths = KnowledgePaths(PROJECT_ROOT)
    try:
        chunks = build_chunks(paths)
        source_count = len(discover_markdown_sources(paths))
        print(f"Markdown files loaded: {source_count}")
        print(f"Valid chunks created: {len(chunks)}")
        if args.dry_run:
            print("Dry run complete: OpenAI was not called and Chroma was not changed.")
            return 0

        if not os.environ.get("OPENAI_API_KEY"):
            print(
                "Rebuild not started: OPENAI_API_KEY is not set. No collection was deleted.",
                file=sys.stderr,
            )
            return 2

        report = rebuild_index(paths, chunks)
    except Exception as exc:
        print(f"Rebuild failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Old application collections removed: "
        + (", ".join(report.removed_collections) or "none")
    )
    print(f"Final collection name: {report.final_collection_name}")
    print(f"Final document count: {report.final_document_count}")
    print(f"Projects indexed: {', '.join(report.projects_indexed)}")
    print(f"Persistence path: {report.persistence_path}")
    for warning in report.warnings:
        print(f"Warning: {warning}")
    print(f"Rebuild complete: exactly one {COLLECTION_NAME} collection is active.")
    print("Restart the local Gradio app after rebuilding so it opens the fresh Chroma index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
