from __future__ import annotations

import unittest
from pathlib import Path

from app.public_facts import (
    load_public_facts,
    lookup_capability_evidence,
    lookup_exact_public_fact,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PublicFactsTests(unittest.TestCase):
    def test_current_employment_is_extracted_from_present_experience_record(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)

        self.assertEqual(len(facts.current_employment), 1)
        employment = facts.current_employment[0]
        self.assertEqual(employment.role, "Web Developer")
        self.assertEqual(employment.organization, "Racetronix")
        self.assertEqual(employment.period, "Jan 2021 - Present")
        self.assertEqual(
            employment.source_title,
            "Ace Relano's Complete Portfolio-Listed Career Timeline",
        )
        self.assertEqual(
            employment.source_url,
            "https://ace-relano-portfolio.vercel.app/about",
        )
        self.assertEqual(employment.source_filename, "knowledge/career-timeline.md")

    def test_profile_location_and_contact_facts_are_derived_from_sources(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)

        self.assertIsNotNone(facts.profile)
        self.assertIn("E-commerce & ERP Developer", facts.profile.role)
        self.assertEqual(facts.listed_location.location, "Pampanga, Philippines")
        self.assertEqual(facts.contact_details.email, "relano.aceheart@gmail.com")
        self.assertEqual(
            facts.contact_details.linkedin_url,
            "https://www.linkedin.com/in/ace-heart-relano-a52311139/",
        )
        self.assertEqual(facts.contact_details.github_url, "https://github.com/ahrelano")

    def test_broad_profile_leads_with_current_development_identity_and_projects(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)

        answer = lookup_exact_public_fact("tell me something about ace", facts)

        self.assertEqual(answer.route, "structured_profile")
        self.assertIn("AI Engineer / E-commerce & ERP Developer", answer.text)
        self.assertIn("Web Developer at Racetronix", answer.text)
        self.assertIn("Odoo 18 Commerce Platform", answer.text)
        self.assertNotIn("graphic", answer.text.casefold())

    def test_complete_timeline_preserves_source_derived_fields_and_operations(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)

        self.assertEqual(len(facts.employment_timeline), 5)
        earliest = facts.earliest_employment()
        self.assertEqual(earliest.role, "Associate Software Engineer Trainee")
        self.assertEqual(earliest.organization, "Cloudstaff")
        self.assertEqual(earliest.start_date, "Nov 2016")
        self.assertEqual(earliest.end_date, "Mar 2017")
        self.assertTrue(earliest.summary)
        self.assertTrue(earliest.highlights)
        self.assertEqual(
            earliest.source_title,
            "Ace Relano's Complete Portfolio-Listed Career Timeline",
        )
        self.assertEqual(
            [record.organization for record in facts.previous_employment()],
            [
                "CV Services Group (Shore 360)",
                "Office Beacon Philippines Inc",
                "Sutherland",
                "Cloudstaff",
            ],
        )
        self.assertEqual(
            facts.employment_by_organization("Office Beacon")[0].role,
            "Graphic Artist",
        )
        self.assertEqual(len(facts.employment_by_role("Graphic Artist")), 2)

    def test_capabilities_and_project_summaries_are_typed_source_facts(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)
        capability_items = {
            item.casefold() for group in facts.capabilities for item in group.items
        }

        self.assertTrue(
            {
                "photo editing",
                "graphic design",
                "sign photography editing",
                "realistic mockups",
                "vector graphics",
                "product mockups",
                "javascript",
                "html & css",
                "bigcommerce",
                "odoo 18 community",
                "technical evaluation",
                "technical leadership",
            }.issubset(capability_items)
        )
        self.assertEqual(len(facts.projects), 3)
        self.assertEqual(
            [project.project_id for project in facts.projects],
            [
                "odoo-18-ecommerce-erp-implementation",
                "bigcommerce-acumatica-integration",
                "acumatica-azure-staging-environment",
            ],
        )
        self.assertTrue(all(project.summary for project in facts.projects))
        self.assertTrue(all(project.source_url for project in facts.projects))

    def test_deterministic_timeline_answers_calibrate_earliest_claim(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)

        start = lookup_exact_public_fact("when did he start working", facts)
        first = lookup_exact_public_fact("what was his first job", facts)

        self.assertEqual(start.route, "structured_timeline")
        self.assertEqual(
            start.text,
            "The earliest role listed in Ace’s portfolio begins in November 2016: "
            "Associate Software Engineer Trainee at Cloudstaff. The portfolio does not "
            "establish whether this was his absolute first-ever job.",
        )
        self.assertIn("November 2016 to March 2017", first.text)
        self.assertIn("earliest portfolio-listed role", first.text)

    def test_specific_capability_lookup_uses_skill_and_experience_evidence(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)

        photo = lookup_capability_evidence("can he help me edit a photo", facts)
        design = lookup_capability_evidence("so he does not know graphic design", facts)

        self.assertEqual(photo.route, "structured_capability")
        self.assertIn("photo-editing", photo.text)
        self.assertIn("Graphic Artist", photo.text)
        self.assertTrue(any("edited sign photography" in item.casefold() for item in photo.evidence))
        self.assertTrue(any("corrected colors" in item for item in photo.evidence))
        self.assertIn("Photo editing", photo.evidence)
        self.assertIn("does not verify whether he is available", photo.text)
        self.assertIn("assumption is not supported", design.text)
        self.assertIn("vector graphics and product mockups", design.text)

    def test_generic_capability_lookup_checks_facts_and_experience(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)

        answer = lookup_capability_evidence("does ace know javascript", facts)

        self.assertEqual(answer.route, "structured_capability")
        self.assertIn("JavaScript", answer.evidence)
        self.assertTrue(any("HTML, CSS, and JavaScript" in item for item in answer.evidence))

    def test_contact_aliases_and_non_development_capabilities_are_natural_and_complete(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)
        for question in (
            "how can i contact ace",
            "how can i reach him",
            "how can i get in touch with ace",
            "where can i message him",
        ):
            with self.subTest(question=question):
                answer = lookup_exact_public_fact(question, facts)
                self.assertEqual(answer.route, "structured_contact")
                self.assertIn("relano.aceheart@gmail.com", answer.text)
                self.assertIn("linkedin.com", answer.text)
                self.assertIn("github.com", answer.text)

        answer = lookup_capability_evidence(
            "aside from development work what else can he do", facts
        )
        self.assertEqual(answer.route, "structured_capability")
        for phrase in (
            "graphic design",
            "photo editing",
            "customer service",
            "data-analysis",
            "technical project leadership",
        ):
            self.assertIn(phrase, answer.text.casefold())
        self.assertNotIn("documents capability with", answer.text.casefold())

    def test_all_five_portfolio_career_ordinals_are_deterministic(self) -> None:
        facts = load_public_facts(PROJECT_ROOT)
        expected = (
            ("first", "Associate Software Engineer Trainee", "Cloudstaff"),
            ("second", "Customer Service Representative", "Sutherland"),
            ("third", "Graphic Artist", "Office Beacon Philippines Inc"),
            ("fourth", "Graphic Artist", "CV Services Group (Shore 360)"),
            ("fifth", "Web Developer", "Racetronix"),
        )
        for ordinal, role, organization in expected:
            with self.subTest(ordinal=ordinal):
                answer = lookup_exact_public_fact(
                    f"what was his {ordinal} portfolio listed job", facts
                )
                self.assertEqual(answer.route, "structured_timeline")
                self.assertIn(role, answer.text)
                self.assertIn(organization, answer.text)


if __name__ == "__main__":
    unittest.main()
