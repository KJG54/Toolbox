from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolbox.timeline_review import TimelineReviewError, answer_timeline, write_answer


class TimelineReviewTests(unittest.TestCase):
    def _timeline(self, directory: Path) -> Path:
        path = directory / "review.json"
        path.write_text(json.dumps({
            "format": "toolbox-watch-review/v1",
            "evidence_timeline": [
                {"kind": "transcript", "start_seconds": 4.5, "end_seconds": 7.5, "text": "The colorful calibration bars appear."},
                {"kind": "frame", "timestamp_seconds": 5.0, "ocr_text": "CALIBRATION"},
                {"kind": "transcript", "start_seconds": 9.0, "end_seconds": 10.0, "text": "The test pattern begins."},
            ],
        }), encoding="utf-8")
        return path

    def test_question_returns_timestamped_local_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = answer_timeline(self._timeline(Path(temporary)), "When do calibration bars appear?")
        self.assertEqual(result["status"], "EVIDENCE_FOUND")
        self.assertEqual(result["citations"][0]["timestamp"], "00:04")
        self.assertIn("calibration", result["citations"][0]["matched_terms"])

    def test_unrepresented_question_does_not_infer_an_answer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = answer_timeline(self._timeline(Path(temporary)), "Who is speaking?")
        self.assertEqual(result["status"], "NO_MATCHING_EVIDENCE")
        self.assertEqual(result["citations"], [])

    def test_rejects_non_timeline_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(TimelineReviewError, "toolbox-watch-review"):
                answer_timeline(path, "When?")

    def test_answer_write_preserves_source_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._timeline(directory)
            original = source.read_text(encoding="utf-8")
            answer = answer_timeline(source, "When do calibration bars appear?")
            output = write_answer(answer, source, directory / "answer.json")
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["status"], "EVIDENCE_FOUND")
