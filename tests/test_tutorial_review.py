from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolbox.tutorial_review import verify_tutorial, write_tutorial_review


class TutorialReviewTests(unittest.TestCase):
    def _inputs(self, directory: Path, steps: list[dict]) -> tuple[Path, Path]:
        timeline = directory / "tutorial.json"
        steps_path = directory / "steps.json"
        timeline.write_text(json.dumps({
            "format": "toolbox-watch-review/v1",
            "evidence_timeline": [
                {"kind": "transcript", "start_seconds": 1, "end_seconds": 2, "text": "Open the project settings panel."},
                {"kind": "frame", "timestamp_seconds": 5, "ocr_text": "EXPORT OPTIONS"},
                {"kind": "transcript", "start_seconds": 9, "end_seconds": 10, "text": "Click save to apply the change."},
            ],
        }), encoding="utf-8")
        steps_path.write_text(json.dumps({"format": "toolbox-ui-tutorial-steps/v1", "steps": steps}), encoding="utf-8")
        return timeline, steps_path

    def test_verifies_ordered_steps_with_citations(self) -> None:
        steps = [
            {"id": "settings", "required_terms": ["project", "settings"]},
            {"id": "export", "required_terms": ["export", "options"]},
            {"id": "save", "any_of_terms": ["save", "apply"]},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            review = verify_tutorial(*self._inputs(Path(temporary), steps))
        self.assertEqual(review["overall_status"], "PASS")
        self.assertEqual(review["findings"][1]["citations"][0]["timestamp_seconds"], 5)

    def test_reports_out_of_order_and_preserves_source(self) -> None:
        steps = [
            {"id": "export", "required_terms": ["export", "options"]},
            {"id": "settings", "required_terms": ["project", "settings"]},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            timeline, steps_path = self._inputs(directory, steps)
            original = timeline.read_text(encoding="utf-8")
            review = verify_tutorial(timeline, steps_path)
            output = write_tutorial_review(review, timeline, directory / "result.json")
            self.assertEqual(review["overall_status"], "OUT_OF_ORDER")
            self.assertEqual(review["findings"][1]["status"], "OUT_OF_ORDER")
            self.assertEqual(timeline.read_text(encoding="utf-8"), original)
            self.assertTrue(output.is_file())
