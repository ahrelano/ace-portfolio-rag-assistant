"""Typed facts and deterministic lookups derived from approved portfolio sources."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document

from app.knowledge import KnowledgePaths, load_source_documents


@dataclass(frozen=True)
class ProfileFact:
    name: str
    display_name: str
    role: str
    headline: str
    introduction: str
    background: str
    source_title: str
    source_url: str
    source_filename: str


@dataclass(frozen=True)
class CapabilityGroupFact:
    title: str
    description: str
    items: tuple[str, ...]
    source_title: str
    source_url: str
    source_filename: str


@dataclass(frozen=True)
class EmploymentFact:
    role: str
    organization: str
    location: str
    period: str
    start_date: str
    end_date: str
    summary: str
    highlights: tuple[str, ...]
    source_title: str
    source_url: str
    source_filename: str


@dataclass(frozen=True)
class ProjectSummaryFact:
    project_id: str
    project_order: int
    title: str
    stage: str | None
    summary: str
    outcome: str | None
    technologies: tuple[str, ...]
    source_title: str
    source_url: str
    source_filename: str


@dataclass(frozen=True)
class ListedLocationFact:
    location: str
    source_title: str
    source_url: str
    source_filename: str


@dataclass(frozen=True)
class ContactDetailsFact:
    email: str | None
    linkedin_url: str | None
    github_url: str | None
    source_title: str
    source_url: str
    source_filename: str


@dataclass(frozen=True)
class FactAnswer:
    route: str
    text: str
    evidence: tuple[str, ...]
    citation_label: str
    source_url: str
    additional_citations: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PublicFacts:
    profile: ProfileFact | None
    capabilities: tuple[CapabilityGroupFact, ...]
    employment_timeline: tuple[EmploymentFact, ...]
    current_employment: tuple[EmploymentFact, ...]
    projects: tuple[ProjectSummaryFact, ...]
    listed_location: ListedLocationFact | None
    contact_details: ContactDetailsFact | None

    def earliest_employment(self) -> EmploymentFact | None:
        return self.employment_timeline[0] if self.employment_timeline else None

    def previous_employment(self) -> tuple[EmploymentFact, ...]:
        return tuple(
            record
            for record in reversed(self.employment_timeline)
            if record.end_date.casefold() != "present"
        )

    def employment_by_organization(self, organization: str) -> tuple[EmploymentFact, ...]:
        query = _normalize(organization)
        return tuple(
            record
            for record in self.employment_timeline
            if query in _normalize(record.organization)
            or _normalize(record.organization) in query
        )

    def employment_by_role(self, role: str) -> tuple[EmploymentFact, ...]:
        query = _normalize(role)
        return tuple(
            record
            for record in self.employment_timeline
            if query in _normalize(record.role) or _normalize(record.role) in query
        )


@lru_cache(maxsize=4)
def load_public_facts(project_root: Path) -> PublicFacts:
    """Load exact public facts once from validated approved Markdown sources."""
    resolved_root = project_root.resolve()
    documents = load_source_documents(KnowledgePaths(resolved_root))
    by_type = {
        str(document.metadata["document_type"]): document
        for document in documents
        if document.metadata["document_type"] != "project"
    }
    timeline = _employment_facts(by_type.get("career"))
    projects = tuple(
        sorted(
            (
                _project_summary_fact(document)
                for document in documents
                if str(document.metadata.get("document_type")) == "project"
            ),
            key=lambda project: project.project_order,
        )
    )
    return PublicFacts(
        profile=_profile_fact(by_type.get("profile")),
        capabilities=_capability_facts(by_type.get("capabilities")),
        employment_timeline=timeline,
        current_employment=tuple(
            record for record in timeline if record.end_date.casefold() == "present"
        ),
        projects=projects,
        listed_location=_listed_location_fact(by_type.get("profile")),
        contact_details=_contact_details_fact(by_type.get("contact")),
    )


def lookup_exact_public_fact(normalized_question: str, facts: PublicFacts) -> FactAnswer | None:
    """Resolve exact profile, timeline, project, location, and contact questions."""
    if answer := _timeline_answer(normalized_question, facts):
        return answer
    if _is_role_correction_question(normalized_question) and facts.profile:
        current_role = facts.current_employment[0] if facts.current_employment else None
        current_text = (
            f" His current portfolio-listed employment is {current_role.role} at "
            f"{current_role.organization} from {_natural_period(current_role)}."
            if current_role
            else ""
        )
        return FactAnswer(
            route="structured_profile",
            text=(
                f"Yes. Ace’s portfolio identifies him as {facts.profile.role}.{current_text} "
                "Graphic design is documented as earlier career experience, while his current "
                "professional identity centers on software development, e-commerce, ERP, "
                "technical leadership, and AI engineering."
            ),
            evidence=(facts.profile.role,),
            citation_label="About Ace",
            source_url=facts.profile.source_url,
        )
    if _is_profile_question(normalized_question) and facts.profile:
        profile = facts.profile
        current_role = facts.current_employment[0] if facts.current_employment else None
        current_text = (
            f" He is currently listed as a {current_role.role} at {current_role.organization} "
            f"from {_natural_period(current_role)}."
            if current_role
            else ""
        )
        project_titles = tuple(project.title for project in facts.projects)
        projects_text = (
            " Strong public projects include " + ", ".join(project_titles) + "."
            if project_titles
            else ""
        )
        work_url = facts.projects[0].source_url if facts.projects else ""
        return FactAnswer(
            route="structured_profile",
            text=(
                f"{profile.display_name} is an {profile.role}. His current professional focus "
                "is software development across e-commerce, ERP, cloud infrastructure, technical "
                f"leadership, and AI engineering.{current_text}{projects_text}"
            ),
            evidence=(profile.role, *project_titles),
            citation_label="About Ace",
            source_url=profile.source_url,
            additional_citations=(("View Ace’s work", work_url),) if work_url else (),
        )
    if _is_professional_role_question(normalized_question) and facts.profile:
        return FactAnswer(
            route="structured_profile",
            text=f"Ace’s portfolio lists his professional role as {facts.profile.role}.",
            evidence=(facts.profile.role,),
            citation_label="About Ace",
            source_url=facts.profile.source_url,
        )
    if _is_location_question(normalized_question):
        if facts.listed_location is None:
            return None
        return FactAnswer(
            route="structured_location",
            text=(
                f"Ace’s portfolio lists his location as {facts.listed_location.location}. "
                "It does not provide real-time location information."
            ),
            evidence=(facts.listed_location.location,),
            citation_label="About Ace",
            source_url=facts.listed_location.source_url,
        )
    if _is_contact_question(normalized_question):
        return _contact_answer(normalized_question, facts.contact_details)
    if _is_project_list_question(normalized_question) and facts.projects:
        summaries = "; ".join(
            f"{project.title}: {project.summary}" for project in facts.projects
        )
        return FactAnswer(
            route="structured_projects",
            text=f"Ace’s portfolio lists these projects: {summaries}",
            evidence=tuple(project.title for project in facts.projects),
            citation_label="View Ace’s work",
            source_url=facts.projects[0].source_url,
        )
    return None


def lookup_capability_evidence(
    normalized_question: str, facts: PublicFacts
) -> FactAnswer | None:
    """Resolve aggregate or specific documented skills from capabilities and work evidence."""
    if _is_non_development_capability_question(normalized_question):
        graphic_roles = facts.employment_by_role("Graphic Artist")
        customer_service = facts.employment_by_role("Customer Service Representative")
        if not graphic_roles or not customer_service or not facts.profile:
            return None
        return FactAnswer(
            route="structured_capability",
            text=(
                "Aside from development, Ace’s portfolio documents graphic design and photo "
                "editing, customer service and technical troubleshooting, data-analysis "
                "training, and technical project leadership. His Graphic Artist work included "
                "sign photography editing, realistic mockups, vector graphics, and product "
                "mockups; his customer-service role included phone and chat support, order "
                "processing, and transaction handling."
            ),
            evidence=(
                "Graphic Artist",
                "photo editing",
                "Customer Service Representative",
                "data analysis",
                "Technical Project Lead",
            ),
            citation_label="About Ace",
            source_url=facts.profile.source_url,
        )
    if _is_broad_capability_synthesis(normalized_question):
        return None

    if _is_aggregate_skills_question(normalized_question):
        if not facts.capabilities:
            return None
        rendered = "; ".join(
            f"{group.title}: {', '.join(group.items)}" for group in facts.capabilities
        )
        return FactAnswer(
            route="structured_capability",
            text=f"Ace’s documented skills include {rendered}.",
            evidence=tuple(
                item for group in facts.capabilities for item in group.items
            ),
            citation_label="About Ace",
            source_url=facts.capabilities[0].source_url,
        )

    if _is_photo_editing_question(normalized_question):
        records = facts.employment_by_role("Graphic Artist")
        capability_evidence = _matching_capability_items(
            facts, ("photo", "photograph", "graphic design", "mockup")
        )
        experience_evidence = tuple(
            highlight
            for record in records
            for highlight in (record.summary, *record.highlights)
            if any(term in _normalize(highlight) for term in ("photo", "photograph", "mockup"))
        )
        evidence = capability_evidence + experience_evidence
        preferred_evidence = next(
            (
                item
                for item in experience_evidence
                if "edited" in _normalize(item)
            ),
            next(
                (
                    item
                    for item in experience_evidence
                    if any(term in _normalize(item) for term in ("photo", "photograph"))
                ),
                experience_evidence[0] if experience_evidence else "",
            ),
        )
        if not records or not evidence or not preferred_evidence:
            return None
        availability = ""
        if any(term in normalized_question for term in ("help me", "available", "suitable")):
            availability = (
                " The portfolio does not verify whether he is available or suitable for your "
                "specific request."
            )
        return FactAnswer(
            route="structured_capability",
            text=(
                "Ace has documented photo-editing and graphic-design experience through his "
                f"Graphic Artist work, including {preferred_evidence.rstrip('.').lower()}."
                f"{availability}"
            ),
            evidence=evidence,
            citation_label="About Ace",
            source_url=records[0].source_url,
        )

    if _is_graphic_design_question(normalized_question):
        records = facts.employment_by_role("Graphic Artist")
        capability_evidence = _matching_capability_items(
            facts, ("graphic design", "vector", "mockup", "photo")
        )
        experience_evidence = tuple(
            highlight
            for record in records
            for highlight in (record.summary, *record.highlights)
            if any(
                term in _normalize(highlight)
                for term in ("graphic", "visual", "vector", "mockup", "typography")
            )
        )
        evidence = capability_evidence + experience_evidence
        if not records or not evidence:
            return None
        preferred_evidence = next(
            (
                item
                for item in experience_evidence
                if any(term in _normalize(item) for term in ("vector", "mockup"))
            ),
            experience_evidence[0] if experience_evidence else "",
        )
        correction = (
            "That assumption is not supported. "
            if any(term in normalized_question for term in ("does not know", "doesn t know", "no knowledge"))
            else ""
        )
        return FactAnswer(
            route="structured_capability",
            text=(
                f"{correction}Ace’s portfolio documents graphic-design experience through "
                f"his {records[0].role} roles, including "
                f"{preferred_evidence.rstrip('.').lower()}."
            ),
            evidence=evidence,
            citation_label="About Ace",
            source_url=records[0].source_url,
        )

    capability_matches = _explicit_capability_matches(normalized_question, facts)
    if capability_matches:
        matched_items = tuple(
            item for group, items in capability_matches for item in (items or (group.title,))
        )
        keywords = {
            token
            for item in matched_items
            for token in _normalize(item).split()
            if len(token) >= 3 and token not in {"and", "systems"}
        }
        experience_evidence = tuple(
            detail
            for record in facts.employment_timeline
            for detail in (record.summary, *record.highlights)
            if any(keyword in _normalize(detail).split() for keyword in keywords)
        )
        rendered = ", ".join(matched_items[:6])
        experience_text = (
            f" His documented experience includes {experience_evidence[0]}"
            if experience_evidence
            else ""
        )
        availability = (
            " The portfolio does not verify whether he is available or suitable for your "
            "specific request."
            if any(term in normalized_question for term in ("help me", "available", "suitable"))
            else ""
        )
        return FactAnswer(
            route="structured_capability",
            text=(
                f"Ace has documented experience with {rendered}."
                f"{experience_text}{availability}"
            ),
            evidence=matched_items + experience_evidence,
            citation_label="About Ace",
            source_url=capability_matches[0][0].source_url,
        )
    return None


def _matching_capability_items(
    facts: PublicFacts, terms: tuple[str, ...]
) -> tuple[str, ...]:
    return tuple(
        item
        for group in facts.capabilities
        for item in group.items
        if any(term in _normalize(item) for term in terms)
    )


def _explicit_capability_matches(
    normalized_question: str, facts: PublicFacts
) -> tuple[tuple[CapabilityGroupFact, tuple[str, ...]], ...]:
    matches: list[tuple[CapabilityGroupFact, tuple[str, ...]]] = []
    for group in facts.capabilities:
        group_name = _normalize(group.title)
        matched_items = tuple(
            item
            for item in group.items
            if _capability_phrase_matches(_normalize(item), normalized_question)
        )
        if matched_items or _capability_phrase_matches(group_name, normalized_question):
            matches.append((group, matched_items))
    return tuple(matches)


def _capability_phrase_matches(capability: str, question: str) -> bool:
    if capability in question:
        return True
    words = capability.split()
    return len(words) > 1 and all(word in question.split() for word in words if len(word) >= 3)


def _timeline_answer(normalized_question: str, facts: PublicFacts) -> FactAnswer | None:
    ordinal = _career_ordinal(normalized_question)
    if ordinal is not None and len(facts.employment_timeline) >= ordinal:
        employment = facts.employment_timeline[ordinal - 1]
        qualifier = (
            " This is the earliest portfolio-listed role; the portfolio does not establish "
            "whether it was his absolute first-ever job."
            if ordinal == 1
            else ""
        )
        return _employment_answer(
            "structured_timeline",
            (
                f"Ace’s {ordinal_label(ordinal)} portfolio-listed job in chronological order "
                f"is {employment.role} at {employment.organization}, "
                f"{_natural_range(employment)}.{qualifier}"
            ),
            employment,
        )
    if _is_current_employment_question(normalized_question):
        if not facts.current_employment:
            return None
        employment = facts.current_employment[0]
        period = _natural_period(employment)
        if "working right now" in normalized_question:
            text = (
                "I can’t know whether Ace is working at this exact moment. However, his "
                f"portfolio lists him as currently employed as a {employment.role} at "
                f"{employment.organization} from {period}."
            )
        elif _is_unemployed_assumption(normalized_question):
            text = (
                "His portfolio indicates that he is currently employed. It lists him as a "
                f"{employment.role} at {employment.organization} from {period}."
            )
        elif "who" in normalized_question and "work for" in normalized_question:
            text = (
                f"Ace’s portfolio lists his current employer as {employment.organization}, "
                f"where he is a {employment.role} from {period}."
            )
        else:
            text = (
                "His portfolio indicates that he is currently employed as a "
                f"{employment.role} at {employment.organization} from {period}."
            )
        return _employment_answer("structured_timeline", text, employment)

    if _is_career_journey_question(normalized_question) and facts.employment_timeline:
        rendered = "; ".join(
            f"{index}. {record.role} at {record.organization} ({_natural_range(record)})"
            for index, record in enumerate(facts.employment_timeline, start=1)
        )
        first = facts.employment_timeline[0]
        return _employment_answer(
            "structured_timeline",
            (
                "Ace’s portfolio-listed career journey, from earliest to current, is: "
                f"{rendered}. The first role is the earliest job listed in the portfolio, "
                "not necessarily his absolute first-ever job."
            ),
            first,
            evidence=tuple(record.role for record in facts.employment_timeline),
        )

    earliest = facts.earliest_employment()
    if earliest and _is_work_start_question(normalized_question):
        text = (
            f"The earliest role listed in Ace’s portfolio begins in "
            f"{_natural_date(earliest.start_date)}: {earliest.role} at "
            f"{earliest.organization}. The portfolio does not establish whether this was his "
            "absolute first-ever job."
        )
        return _employment_answer("structured_timeline", text, earliest)
    if earliest and _is_first_job_question(normalized_question):
        text = (
            f"The earliest portfolio-listed role is {earliest.role} at "
            f"{earliest.organization}, {_natural_range(earliest)}. The portfolio does not "
            "establish whether this was his absolute first-ever job."
        )
        return _employment_answer("structured_timeline", text, earliest)

    organization_records = _matching_organization_records(normalized_question, facts)
    if organization_records:
        record = organization_records[0]
        details = "; ".join((record.summary, *record.highlights))
        return _employment_answer(
            "structured_timeline",
            f"At {record.organization}, Ace worked as a {record.role}, "
            f"{_natural_range(record)}. {details}",
            record,
        )

    role_records = _matching_role_records(normalized_question, facts)
    if role_records:
        rendered = "; ".join(
            f"{record.role} at {record.organization} ({_natural_range(record)})"
            for record in role_records
        )
        return _employment_answer(
            "structured_timeline",
            f"Yes. Ace’s portfolio lists this documented experience: {rendered}.",
            role_records[0],
            evidence=tuple(record.role for record in role_records),
        )

    if _is_previous_employment_question(normalized_question):
        records = facts.previous_employment()
        if not records:
            return None
        rendered = "; ".join(
            f"{record.role} at {record.organization} ({_natural_range(record)})"
            for record in records
        )
        return _employment_answer(
            "structured_timeline",
            f"Before his current role, Ace’s portfolio lists: {rendered}.",
            records[0],
            evidence=tuple(record.role for record in records),
        )
    return None


def _employment_answer(
    route: str,
    text: str,
    record: EmploymentFact,
    *,
    evidence: tuple[str, ...] | None = None,
) -> FactAnswer:
    return FactAnswer(
        route=route,
        text=text,
        evidence=evidence or (record.role, record.organization, record.period, *record.highlights),
        citation_label="About Ace",
        source_url=record.source_url,
    )


def _contact_answer(
    normalized_question: str, contact: ContactDetailsFact | None
) -> FactAnswer | None:
    if contact is None:
        return None
    details: list[str] = []
    if "email" in normalized_question and contact.email:
        details.append(f"Ace’s public email is {contact.email}.")
    elif "linkedin" in normalized_question and contact.linkedin_url:
        details.append(f"Ace’s public LinkedIn is {contact.linkedin_url}.")
    elif "github" in normalized_question and contact.github_url:
        details.append(f"Ace’s public GitHub is {contact.github_url}.")
    else:
        if contact.email:
            details.append(f"You can contact Ace at {contact.email}.")
        if contact.linkedin_url:
            details.append(f"LinkedIn: {contact.linkedin_url}.")
        if contact.github_url:
            details.append(f"GitHub: {contact.github_url}.")
    if not details:
        return None
    return FactAnswer(
        route="structured_contact",
        text=" ".join(details),
        evidence=tuple(details),
        citation_label="Contact Ace",
        source_url=contact.source_url,
    )


def _profile_fact(document: Document | None) -> ProfileFact | None:
    if document is None:
        return None
    values = (
        _bullet_value(document.page_content, "Name"),
        _bullet_value(document.page_content, "Display name"),
        _bullet_value(document.page_content, "Role"),
        _section_text(document.page_content, "Headline"),
        _section_text(document.page_content, "Introduction"),
        _section_text(document.page_content, "Background"),
    )
    if any(value is None for value in values):
        return None
    name, display_name, role, headline, introduction, background = values
    return ProfileFact(
        name=str(name),
        display_name=str(display_name),
        role=str(role),
        headline=str(headline),
        introduction=str(introduction),
        background=str(background),
        **_source_fields(document),
    )


def _capability_facts(document: Document | None) -> tuple[CapabilityGroupFact, ...]:
    if document is None:
        return ()
    groups: list[CapabilityGroupFact] = []
    for heading, body in _heading_blocks(document.page_content):
        description = next(
            (
                line.strip()
                for line in body.splitlines()
                if line.strip() and not line.lstrip().startswith("-")
            ),
            "",
        )
        items = tuple(
            line.strip().removeprefix("- ").strip()
            for line in body.splitlines()
            if line.strip().startswith("- ")
        )
        if items:
            groups.append(
                CapabilityGroupFact(
                    title=heading,
                    description=description,
                    items=items,
                    **_source_fields(document),
                )
            )
    return tuple(groups)


def _employment_facts(document: Document | None) -> tuple[EmploymentFact, ...]:
    if document is None:
        return ()
    records: list[EmploymentFact] = []
    for heading, body in _heading_blocks(document.page_content):
        normalized_heading = re.sub(r"^\d+\.\s*", "", heading)
        role_and_organization = re.fullmatch(
            r"(.+?)\s+[—–-]\s+(.+)", normalized_heading
        )
        period = _bullet_value(body, "Period")
        if role_and_organization is None or period is None:
            continue
        start_date, end_date = _split_period(period)
        descriptive_bullets = tuple(
            line.strip().removeprefix("- ").strip()
            for line in body.splitlines()
            if line.strip().startswith("- ")
            and not re.match(r"(?i)^(?:Location|Period)\s*:", line.strip().removeprefix("- "))
        )
        narrative_sentences = tuple(
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", _first_paragraph(body))
            if sentence.strip()
        )
        records.append(
            EmploymentFact(
                role=role_and_organization.group(1).strip(),
                organization=role_and_organization.group(2).strip(),
                location=_bullet_value(body, "Location") or "",
                period=period,
                start_date=start_date,
                end_date=end_date,
                summary=(narrative_sentences[0] if narrative_sentences else "") or (
                    descriptive_bullets[0] if descriptive_bullets else ""
                ),
                highlights=narrative_sentences[1:] + descriptive_bullets,
                **_source_fields(document),
            )
        )
    return tuple(sorted(records, key=lambda record: _date_key(record.start_date)))


def _project_summary_fact(document: Document) -> ProjectSummaryFact:
    blocks = dict(_heading_blocks(document.page_content))
    summary_body = blocks.get("Summary", "")
    summary = _first_paragraph(summary_body)
    technologies = tuple(
        line.strip().removeprefix("- ").strip()
        for line in blocks.get("Technologies", "").splitlines()
        if line.strip().startswith("- ")
    )
    return ProjectSummaryFact(
        project_id=str(document.metadata["project_id"]),
        project_order=int(document.metadata["project_order"]),
        title=str(document.metadata["document_title"]),
        stage=None,
        summary=summary,
        outcome=_first_paragraph(blocks.get("Results or current status", "")) or None,
        technologies=technologies,
        **_source_fields(document),
    )


def _listed_location_fact(document: Document | None) -> ListedLocationFact | None:
    if document is None or (location := _bullet_value(document.page_content, "Location")) is None:
        return None
    return ListedLocationFact(location=location, **_source_fields(document))


def _contact_details_fact(document: Document | None) -> ContactDetailsFact | None:
    if document is None:
        return None
    return ContactDetailsFact(
        email=_bullet_value(document.page_content, "Email"),
        linkedin_url=_bullet_value(document.page_content, "LinkedIn"),
        github_url=_bullet_value(document.page_content, "GitHub"),
        **_source_fields(document),
    )


def _matching_organization_records(
    normalized_question: str, facts: PublicFacts
) -> tuple[EmploymentFact, ...]:
    return tuple(
        record
        for record in facts.employment_timeline
        if _normalize(record.organization) in normalized_question
        or any(
            token in normalized_question
            for token in _normalize(record.organization).split()
            if len(token) >= 5
        )
    )


def _matching_role_records(
    normalized_question: str, facts: PublicFacts
) -> tuple[EmploymentFact, ...]:
    return tuple(
        record
        for record in facts.employment_timeline
        if _normalize(record.role) in normalized_question
    )


def _is_current_employment_question(question: str) -> bool:
    if _is_unemployed_assumption(question):
        return True
    return any(
        term in question
        for term in (
            "working right now", "working now", "still working",
            "working for a company now", "working on a company now", "currently employed",
            "current employer", "current job", "latest job", "current company",
            "currently have a job", "have a job right now", "has a job right now",
            "work or job right now", "who does he currently work for",
            "who does ace currently work for", "who does he work for", "who does ace work for",
            "where does he currently work", "where does ace currently work", "where does he work",
            "where does ace work", "is he employed", "is ace employed", "what is his work",
            "what is ace work",
        )
    ) and not any(term in question for term in ("responsibilities", "duties", "what does he do at"))


def _is_unemployed_assumption(question: str) -> bool:
    return any(
        term in question
        for term in ("doesn t have a job", "does not have a job", "probably unemployed")
    )


def _is_work_start_question(question: str) -> bool:
    return any(
        term in question
        for term in ("when did he start working", "when did ace start working", "earliest employment")
    )


def _is_first_job_question(question: str) -> bool:
    return any(term in question for term in ("first job", "first role", "earliest job", "earliest role"))


def _is_previous_employment_question(question: str) -> bool:
    return any(
        term in question
        for term in ("work before", "worked before", "previous job", "previous work", "past work")
    )


def _is_career_journey_question(question: str) -> bool:
    return any(
        phrase in question
        for phrase in (
            "career journey",
            "career timeline",
            "employment history",
            "developer journey",
        )
    )


def _is_profile_question(question: str) -> bool:
    return question in {
        "who is ace",
        "what does ace do",
        "what does he do",
        "tell me about ace",
        "tell me something about ace",
        "tell me about him",
        "tell me more about him",
        "what is his background",
        "what is ace s profile",
    }


def _is_role_correction_question(question: str) -> bool:
    return (
        any(term in question for term in ("developer", "ai engineer"))
        and any(term in question for term in ("i thought", "isn t he", "is not he"))
    )


def _is_professional_role_question(question: str) -> bool:
    return any(term in question for term in ("professional role", "portfolio role", "professional title"))


def _is_location_question(question: str) -> bool:
    return any(
        term in question
        for term in (
            "where is ace", "where is he", "where does ace live", "where does he live",
            "current location", "his location", "ace location",
        )
    )


def _is_contact_question(question: str) -> bool:
    return any(
        term in question
        for term in (
            "contact", "email", "linkedin", "github", "reach ace", "reach him",
            "get in touch", "connect with ace", "connect with him", "message ace",
            "message him", "hire ace", "hire him",
        )
    )


def _is_non_development_capability_question(question: str) -> bool:
    return any(
        phrase in question
        for phrase in (
            "aside from development",
            "outside development",
            "other than development",
            "besides development",
            "what else can he do",
            "what else can ace do",
        )
    )


def _career_ordinal(question: str) -> int | None:
    """Return a bounded portfolio-career ordinal without vector interpretation."""
    if not any(term in question for term in ("job", "role", "position", "employment", "one")):
        return None
    ordinal_terms = {
        1: ("first", "1st", "earliest", "starting"),
        2: ("second", "2nd"),
        3: ("third", "3rd"),
        4: ("fourth", "4th"),
        5: ("fifth", "5th"),
    }
    for ordinal, terms in ordinal_terms.items():
        if any(re.search(rf"\b{re.escape(term)}\b", question) for term in terms):
            return ordinal
    return None


def ordinal_label(ordinal: int) -> str:
    return {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth"}[ordinal]


def _is_project_list_question(question: str) -> bool:
    return question in {
        "what projects does ace have",
        "what projects has ace worked on",
        "what projects has he worked on",
        "list ace s projects",
        "list his projects",
    }


def _is_aggregate_skills_question(question: str) -> bool:
    return any(
        phrase in question
        for phrase in (
            "what can ace do",
            "what can he do",
            "what can ace help with",
            "what can he help with",
        )
    ) or (
        any(term in question for term in ("skills", "capabilities", "technologies"))
        and any(term in question for term in ("what", "tell", "list", "which"))
    )


def _is_broad_capability_synthesis(question: str) -> bool:
    return any(
        term in question
        for term in (
            "describe",
            "background combine",
            "best demonstrate",
            "compare",
            "how does",
            "experience with",
            "what is ace s experience",
        )
    )


def _is_photo_editing_question(question: str) -> bool:
    return (
        any(term in question for term in ("photo", "photograph", "image"))
        and any(term in question for term in ("edit", "editing", "edited"))
    )


def _is_graphic_design_question(question: str) -> bool:
    return any(
        term in question
        for term in ("graphic design", "graphic artist", "vector graphic", "product mockup")
    )


def _heading_blocks(content: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", content))
    return [
        (
            match.group(1).strip(),
            content[
                match.end() : matches[index + 1].start()
                if index + 1 < len(matches)
                else len(content)
            ].strip(),
        )
        for index, match in enumerate(matches)
    ]


def _section_text(content: str, heading: str) -> str | None:
    return dict(_heading_blocks(content)).get(heading)


def _section_url(content: str, heading: str) -> str | None:
    body = _section_text(content, heading) or ""
    match = re.search(r"(?m)^\s*-\s*(https?://\S+)\s*$", body)
    return match.group(1).strip() if match else None


def _bullet_value(content: str, label: str) -> str | None:
    match = re.search(
        rf"(?im)^\s*-\s*{re.escape(label)}\s*:\s*(?P<value>[^\r\n]+)", content
    )
    return match.group("value").strip() if match else None


def _first_paragraph(content: str) -> str:
    return next(
        (
            paragraph.replace("\n", " ").strip()
            for paragraph in re.split(r"\n\s*\n", content)
            if paragraph.strip() and not paragraph.lstrip().startswith(("#", "-"))
        ),
        "",
    )


def _split_period(period: str) -> tuple[str, str]:
    parts = re.split(r"\s+[-–—]\s+", period, maxsplit=1)
    return (parts[0].strip(), parts[1].strip()) if len(parts) == 2 else (period, "")


def _date_key(date: str) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Za-z]{3})\s+(\d{4})", date.strip())
    if not match:
        return (9999, 12)
    return (int(match.group(2)), _month_number(match.group(1)))


def _month_number(month: str) -> int:
    months = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
    return months.index(month.casefold()) + 1


def _natural_date(date: str) -> str:
    match = re.fullmatch(r"([A-Za-z]{3})\s+(\d{4})", date.strip())
    if not match:
        return date
    months = {
        "jan": "January", "feb": "February", "mar": "March", "apr": "April",
        "may": "May", "jun": "June", "jul": "July", "aug": "August",
        "sep": "September", "oct": "October", "nov": "November", "dec": "December",
    }
    return f"{months[match.group(1).casefold()]} {match.group(2)}"


def _natural_period(record: EmploymentFact) -> str:
    if record.end_date.casefold() == "present":
        return f"{_natural_date(record.start_date)} to the present"
    return f"{_natural_date(record.start_date)} to {_natural_date(record.end_date)}"


def _natural_range(record: EmploymentFact) -> str:
    return _natural_period(record)


def _normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", text.casefold()).split())


def _source_fields(document: Document) -> dict[str, str]:
    return {
        "source_title": str(document.metadata["document_title"]),
        "source_url": str(document.metadata["source_url"]),
        "source_filename": str(document.metadata["source_filename"]),
    }
