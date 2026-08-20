from __future__ import annotations

import json
import unittest
from pathlib import Path

from langchain_core.documents import Document

from app.chat_service import RetrievedChunk, _accepted_evidence


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "retrieval_calibration.json"


def calibration_chunk(
    section: str, score: float, content: str = "Observed approved portfolio evidence."
) -> RetrievedChunk:
    source = {
        "profile": "knowledge/profile.md",
        "career": "knowledge/career-timeline.md",
        "capabilities": "knowledge/capabilities.md",
        "projects": "knowledge/projects/odoo-18-commerce-platform.md",
    }[section]
    return RetrievedChunk(
        Document(
            page_content=content,
            metadata={
                "source_filename": source,
                "source_url": "https://ace-relano-portfolio.vercel.app/about",
                "section": section,
                "document_title": "Calibration evidence",
            },
        ),
        relevance_score=score,
    )


class RetrievalThresholdCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_observed_scores_support_general_and_section_targeted_thresholds(self) -> None:
        general = self.fixture["general_threshold"]
        targeted = self.fixture["targeted_threshold"]
        relevant_scores = [item["relevance"] for item in self.fixture["relevant"]]
        irrelevant_scores = [item["relevance"] for item in self.fixture["irrelevant"]]

        self.assertTrue(all(score >= targeted for score in relevant_scores))
        self.assertTrue(all(score < general for score in irrelevant_scores))
        self.assertGreater(max(irrelevant_scores), min(relevant_scores))
        for item in (*self.fixture["relevant"], *self.fixture["irrelevant"]):
            self.assertAlmostEqual(
                item["relevance"], 1.0 - item["raw_distance"] / 2.0, places=6
            )

    def test_targeted_threshold_never_admits_a_high_scoring_wrong_section(self) -> None:
        chunks = [
            calibration_chunk("profile", 0.82),
            calibration_chunk("capabilities", 0.73),
            calibration_chunk("projects", 0.706803),
        ]

        accepted = _accepted_evidence(
            chunks,
            "what projects best demonstrate his skills",
            threshold=0.75,
            targeted_threshold=0.70,
        )

        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0].document.metadata["section"], "projects")

    def test_general_questions_keep_the_stricter_threshold(self) -> None:
        chunks = [calibration_chunk("profile", 0.735652)]

        accepted = _accepted_evidence(
            chunks,
            "tell me something broad",
            threshold=0.75,
            targeted_threshold=0.70,
        )

        self.assertEqual(accepted, [])

    def test_targeted_erp_filter_rejects_semantically_close_non_erp_career(self) -> None:
        chunks = [
            calibration_chunk(
                "career", 0.73, "Created vector graphics and product mockups."
            ),
            calibration_chunk(
                "capabilities", 0.72, "ERP systems with Odoo and inventory validation."
            ),
        ]

        accepted = _accepted_evidence(
            chunks,
            "describe ace s erp experience",
            threshold=0.75,
            targeted_threshold=0.70,
        )

        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0].document.metadata["section"], "capabilities")


if __name__ == "__main__":
    unittest.main()
