"""Parse and validate facts from the approved TypeScript portfolio source."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceExperience:
    role: str
    organization: str
    location: str
    period: str
    summary: str
    highlights: tuple[str, ...]


@dataclass(frozen=True)
class SourceCapabilityGroup:
    title: str
    description: str
    items: tuple[str, ...]


@dataclass(frozen=True)
class SourceProject:
    slug: str
    title: str


def parse_approved_portfolio_source(
    source_path: Path,
) -> tuple[tuple[SourceExperience, ...], tuple[SourceCapabilityGroup, ...]]:
    """Read the two generated-knowledge collections from the approved source."""
    source = source_path.read_text(encoding="utf-8")
    experiences = tuple(
        SourceExperience(
            role=_string_field(block, "role"),
            organization=_string_field(block, "organization"),
            location=_string_field(block, "location"),
            period=_string_field(block, "period"),
            summary=_string_field(block, "summary"),
            highlights=_string_array_field(block, "highlights"),
        )
        for block in _object_blocks(_array_field(source, "experience"))
    )
    capabilities = tuple(
        SourceCapabilityGroup(
            title=_string_field(block, "title"),
            description=_string_field(block, "description"),
            items=_string_array_field(block, "items"),
        )
        for block in _object_blocks(_array_field(source, "capabilities"))
    )
    if not experiences or not capabilities:
        raise ValueError(f"{source_path}: missing experience or capabilities data")
    return experiences, capabilities


def parse_approved_projects(source_path: Path) -> tuple[SourceProject, ...]:
    """Return the ordered public project identifiers and titles from portfolio.ts."""
    source = source_path.read_text(encoding="utf-8")
    projects = tuple(
        SourceProject(
            slug=_string_field(block, "slug"),
            title=_string_field(block, "title"),
        )
        for block in _object_blocks(_array_field(source, "projects"))
    )
    if not projects:
        raise ValueError(f"{source_path}: missing project data")
    if len({project.slug for project in projects}) != len(projects):
        raise ValueError(f"{source_path}: duplicate project slugs")
    return projects


def validate_knowledge_against_approved_source(project_root: Path) -> None:
    """Check canonical Markdown coverage without regenerating or rewriting it."""
    source_path = project_root / "input" / "portfolio.ts"
    experiences, capabilities = parse_approved_portfolio_source(source_path)
    projects = parse_approved_projects(source_path)
    source = source_path.read_text(encoding="utf-8")
    profile_source = _object_field(source, "profile")
    profile = (project_root / "knowledge" / "profile.md").read_text(encoding="utf-8")
    contact = (project_root / "knowledge" / "contact.md").read_text(encoding="utf-8")
    education = (
        project_root / "knowledge" / "education-and-certifications.md"
    ).read_text(encoding="utf-8")
    career = (project_root / "knowledge" / "career-timeline.md").read_text(
        encoding="utf-8"
    )
    capability_text = (project_root / "knowledge" / "capabilities.md").read_text(
        encoding="utf-8"
    )

    missing_career_facts = [
        value
        for experience in experiences
        for value in (experience.role, experience.organization, experience.period)
        if value not in career
    ]
    if missing_career_facts:
        raise ValueError(
            "Canonical career Markdown is missing approved facts: "
            f"{sorted(set(missing_career_facts))}"
        )

    missing_profile_facts = [
        value
        for value in (
            _string_field(profile_source, "name"),
            _string_field(profile_source, "displayName"),
            _string_field(profile_source, "role"),
            _string_field(profile_source, "location"),
        )
        if value not in profile
    ]
    if missing_profile_facts:
        raise ValueError(
            "Canonical profile Markdown is missing approved facts: "
            f"{sorted(set(missing_profile_facts))}"
        )

    contact_values = [_string_field(profile_source, "email")]
    for social in _object_blocks(_array_field(source, "socials")):
        contact_values.append(_string_field(social, "href"))
    missing_contact_facts = [value for value in contact_values if value not in contact]
    if missing_contact_facts:
        raise ValueError(
            "Canonical contact Markdown is missing approved facts: "
            f"{sorted(set(missing_contact_facts))}"
        )

    learning_values: list[str] = []
    for learning in _object_blocks(_array_field(source, "learning")):
        learning_values.extend(
            (
                _string_field(learning, "title"),
                _string_field(learning, "institution"),
                _string_field(learning, "period"),
            )
        )
        if credential_url := _optional_string_field(learning, "credentialUrl"):
            learning_values.append(credential_url)
    missing_learning_facts = [value for value in learning_values if value not in education]
    if missing_learning_facts:
        raise ValueError(
            "Canonical education Markdown is missing approved facts: "
            f"{sorted(set(missing_learning_facts))}"
        )

    missing_capability_facts = [
        value
        for group in capabilities
        for value in group.items
        if value not in capability_text
    ]
    if missing_capability_facts:
        raise ValueError(
            "Canonical capability Markdown is missing approved facts: "
            f"{sorted(set(missing_capability_facts))}"
        )

    project_dir = project_root / "knowledge" / "projects"
    project_markdown = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(project_dir.glob("*.md"))
    )
    missing_project_facts = [
        value
        for project in projects
        for value in (project.slug, project.title)
        if value not in project_markdown
    ]
    if missing_project_facts:
        raise ValueError(
            "Canonical project Markdown is missing approved facts: "
            f"{sorted(set(missing_project_facts))}"
        )


def _array_field(text: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*:\s*\[", text)
    if match is None:
        raise ValueError(f"Missing array field: {name}")
    return _balanced_body(text, match.end() - 1, "[", "]")


def _object_field(text: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*:\s*{{", text)
    if match is None:
        raise ValueError(f"Missing object field: {name}")
    return _balanced_body(text, match.end() - 1, "{", "}")


def _string_array_field(text: str, name: str) -> tuple[str, ...]:
    return tuple(_string_literals(_array_field(text, name)))


def _string_field(text: str, name: str) -> str:
    match = re.search(
        rf"\b{re.escape(name)}\s*:\s*\"((?:\\.|[^\"\\])*)\"", text, re.DOTALL
    )
    if match is None:
        raise ValueError(f"Missing string field: {name}")
    return _decode_string(match.group(1))


def _optional_string_field(text: str, name: str) -> str | None:
    match = re.search(
        rf"\b{re.escape(name)}\s*:\s*\"((?:\\.|[^\"\\])*)\"",
        text,
        re.DOTALL,
    )
    return _decode_string(match.group(1)) if match else None


def _string_literals(text: str) -> list[str]:
    return [
        _decode_string(match.group(1))
        for match in re.finditer(r'\"((?:\\.|[^\"\\])*)\"', text, re.DOTALL)
    ]


def _decode_string(value: str) -> str:
    return str(json.loads(f'"{value}"'))


def _object_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    index = 0
    while index < len(text):
        if text[index] == "{":
            blocks.append(_balanced_body(text, index, "{", "}"))
            index = _balanced_end(text, index, "{", "}") + 1
        else:
            index += 1
    return blocks


def _balanced_body(text: str, start: int, opening: str, closing: str) -> str:
    end = _balanced_end(text, start, opening, closing)
    return text[start + 1 : end]


def _balanced_end(text: str, start: int, opening: str, closing: str) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"Unterminated {opening}{closing} block")
