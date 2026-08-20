"""Print bounded Chroma candidate, guard, and final-context diagnostics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.chat_service import (  # noqa: E402
    ChatSettings,
    ChromaPortfolioRetriever,
    TopicPreference,
    _accepted_evidence_for_intents,
    _candidate_rejection_reason,
    _chunk_topic,
    _employment_period,
    _filter_chunks_by_topics,
    _merge_retrieved_chunks,
    _missing_evidence_intents,
    _normalize_question,
    _retrieve_portfolio_candidates,
    _selected_topics,
    _topics_for_intents,
    contextualized_retrieval_query,
    detect_portfolio_intents,
    expand_retrieval_query,
    resolve_follow_up_query,
    resolve_project_focus,
)
from app.public_facts import load_public_facts  # noqa: E402


DEFAULT_QUESTIONS = (
    "Can he help me edit a photo?",
    "Does he have knowledge of graphic design?",
    "Describe Ace's ERP experience.",
    "How does his background combine design and development?",
    "What projects best demonstrate his skills?",
    "I have trouble with my e-commerce. Can Ace help, and how can I reach him?",
    "Give me a recipe for pancakes.",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("questions", nargs="*", default=DEFAULT_QUESTIONS)
    parser.add_argument(
        "--prior-user",
        default="",
        help="Optional latest user message for one conversational retrieval diagnosis.",
    )
    parser.add_argument(
        "--prior-assistant",
        default="",
        help="Optional prior assistant text used only to identify a known project reference.",
    )
    args = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    settings = ChatSettings.from_environment()
    retriever = ChromaPortfolioRetriever(PROJECT_ROOT)
    facts = load_public_facts(PROJECT_ROOT)
    history: list[dict[str, str]] = []
    if args.prior_user:
        history.append({"role": "user", "content": args.prior_user})
    if args.prior_assistant:
        history.append({"role": "assistant", "content": args.prior_assistant})
    for question in args.questions:
        project_focus = resolve_project_focus(question, history, facts)
        standalone_question = resolve_follow_up_query(
            question, history, project_focus=project_focus
        )
        normalized = _normalize_question(standalone_question)
        intents = detect_portfolio_intents(normalized)
        project_retrieval_focus = project_focus
        if "projects" in intents and not project_retrieval_focus:
            project_retrieval_focus = facts.projects
        topics = _selected_topics(normalized, TopicPreference())
        retrieval_query = contextualized_retrieval_query(standalone_question, history)
        first_pass = _retrieve_portfolio_candidates(
            retriever,
            retrieval_query,
            normalized,
            topics=topics,
            candidate_limit=settings.candidate_limit,
            project_focus=project_retrieval_focus,
        )
        accepted_first = _accepted_evidence_for_intents(
            _filter_chunks_by_topics(first_pass, topics),
            normalized,
            intents,
            threshold=settings.relevance_threshold,
            targeted_threshold=settings.targeted_relevance_threshold,
        )
        missing = _missing_evidence_intents(accepted_first, intents)
        retry_ran = not accepted_first or bool(missing)
        candidates = list(first_pass)
        if retry_ran:
            retry_intents = missing or intents
            retry_topics = _topics_for_intents(retry_intents, TopicPreference())
            retry = _retrieve_portfolio_candidates(
                retriever,
                expand_retrieval_query(standalone_question, intents=retry_intents),
                normalized,
                topics=retry_topics,
                candidate_limit=settings.candidate_limit,
                retry_intents=retry_intents,
                project_focus=project_retrieval_focus,
            )
            candidates = _merge_retrieved_chunks(
                (first_pass, retry), limit=settings.candidate_limit
            )
        accepted = _accepted_evidence_for_intents(
            _filter_chunks_by_topics(candidates, topics),
            normalized,
            intents,
            threshold=settings.relevance_threshold,
            targeted_threshold=settings.targeted_relevance_threshold,
        )
        accepted_ids = {id(item) for item in accepted}
        selected_ids = {id(item) for item in accepted[: settings.retrieval_limit]}
        print(f"\nQUERY: {question}")
        print(f"RETRIEVAL_QUERY: {retrieval_query}")
        print(f"NORMALIZED: {normalized}")
        print(f"INTENTS: {', '.join(sorted(intents))}")
        print(f"RETRY_RAN: {retry_ran}")
        for rank, item in enumerate(candidates, start=1):
            metadata = item.document.metadata
            raw_distance = (
                f"{item.raw_distance:.6f}" if item.raw_distance is not None else "unavailable"
            )
            print(
                f"{rank:02d} raw_distance={raw_distance} "
                f"relevance={item.relevance_score:.6f} "
                f"title={metadata.get('document_title', '')!r} "
                f"topic={_chunk_topic(item)} "
                f"section={metadata.get('section', '')} "
                f"period={_employment_period(item.document.page_content)} "
                f"accepted={id(item) in accepted_ids} selected={id(item) in selected_ids} "
                f"rejection={_candidate_rejection_reason(item, accepted_ids=accepted_ids, intents=intents, threshold=settings.relevance_threshold)} "
                f"source={metadata.get('source_filename', '')} "
                f"metadata={{document_type={metadata.get('document_type', '')!r}, "
                f"project_id={metadata.get('project_id', '')!r}, "
                f"semantic_type={metadata.get('semantic_type', '')!r}, "
                f"source_url={metadata.get('source_url', '')!r}}}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
