"""Validate canonical Markdown against the approved input/portfolio.ts source."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.source_sync import validate_knowledge_against_approved_source  # noqa: E402


def main() -> int:
    validate_knowledge_against_approved_source(PROJECT_ROOT)
    print("Canonical portfolio Markdown matches the approved source facts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
