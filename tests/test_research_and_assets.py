from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolbox.asset_discovery import search_asset_sources
from toolbox.capability_research import research_capability, write_research_brief


class ResearchAndAssetTests(unittest.TestCase):
    def test_unknown_capability_returns_review_only_gap(self) -> None:
        brief = research_capability("generate_image", commercial=True, free_only=True)
        self.assertEqual(brief["status"], "CAPABILITY_GAP")
        self.assertEqual(brief["mutations_performed"], [])
        self.assertIn("official project documentation", brief["research_requirements"][0])

    def test_asset_search_filters_to_commercial_safe_source(self) -> None:
        result = search_asset_sources("stone wall texture", kind="texture", commercial=True)
        self.assertEqual([item["id"] for item in result["results"]], ["poly-haven"])
        self.assertEqual(result["external_actions_performed"], [])

    def test_research_brief_never_overwrites_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "gap.json"
            first = research_capability("generate_image")
            write_research_brief(first, output)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["status"], "CAPABILITY_GAP")
            with self.assertRaises(FileExistsError):
                write_research_brief(first, output)
