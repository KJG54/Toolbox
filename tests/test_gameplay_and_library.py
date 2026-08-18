from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolbox.evidence_library import search_library
from toolbox.gameplay_review import review_gameplay


class GameplayAndLibraryTests(unittest.TestCase):
    def _timeline(self, path: Path, text: str) -> None:
        path.write_text(json.dumps({"format": "toolbox-watch-review/v1", "evidence_timeline": [
            {"kind": "transcript", "start_seconds": 2, "end_seconds": 3, "text": text},
            {"kind": "frame", "timestamp_seconds": 7, "ocr_text": "OBJECTIVE COMPLETE"},
        ]}), encoding="utf-8")

    def test_gameplay_review_reports_observed_and_forbidden_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            timeline = directory / "play.json"
            events = directory / "events.json"
            self._timeline(timeline, "The player enters the arena.")
            events.write_text(json.dumps({"format": "toolbox-gameplay-events/v1", "events": [
                {"id": "enter", "required_terms": ["player", "arena"]},
                {"id": "objective", "required_terms": ["objective", "complete"]},
                {"id": "no-crash", "forbidden_terms": ["crash"]},
            ]}), encoding="utf-8")
            result = review_gameplay(timeline, events)
        self.assertEqual(result["overall_status"], "PASS")
        self.assertEqual([item["status"] for item in result["findings"]], ["OBSERVED", "OBSERVED", "OBSERVED"])

    def test_library_searches_multiple_timelines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._timeline(directory / "first.json", "Open the export settings panel.")
            self._timeline(directory / "second.json", "Nothing about export appears here.")
            result = search_library(directory, "Where are export settings?")
        self.assertEqual(result["status"], "EVIDENCE_FOUND")
        self.assertEqual(result["matches"][0]["timeline"].endswith("first.json"), True)
