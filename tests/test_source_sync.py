from __future__ import annotations

import unittest
from pathlib import Path

from app.source_sync import (
    parse_approved_portfolio_source,
    parse_approved_projects,
    validate_knowledge_against_approved_source,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PortfolioSourceSyncTests(unittest.TestCase):
    def test_canonical_markdown_covers_approved_source_facts(self) -> None:
        validate_knowledge_against_approved_source(PROJECT_ROOT)

    def test_source_parser_covers_every_experience_and_required_capability(self) -> None:
        experiences, capability_groups = parse_approved_portfolio_source(
            PROJECT_ROOT / "input" / "portfolio.ts"
        )
        items = {item.casefold() for group in capability_groups for item in group.items}

        self.assertEqual(len(experiences), 5)
        self.assertEqual(experiences[0].period, "Jan 2021 - Present")
        self.assertEqual(experiences[-1].period, "Nov 2016 - Mar 2017")
        self.assertTrue(
            {
                "photo editing",
                "graphic design",
                "javascript",
                "bigcommerce",
                "odoo 18 community",
                "technical leadership",
            }.issubset(items)
        )

    def test_source_parser_preserves_the_approved_project_order(self) -> None:
        projects = parse_approved_projects(PROJECT_ROOT / "input" / "portfolio.ts")
        self.assertEqual(
            [(project.slug, project.title) for project in projects],
            [
                ("odoo-18-ecommerce-erp-implementation", "Odoo 18 Commerce Platform"),
                ("bigcommerce-acumatica-integration", "BigCommerce and Acumatica Integration"),
                ("acumatica-azure-staging-environment", "Acumatica Azure Staging Environment"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
