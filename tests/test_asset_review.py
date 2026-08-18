from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolbox.asset_review import AssetReviewError, assess_timeline, write_assessment


class AssetReviewTests(unittest.TestCase):
    def _inputs(self, directory: Path) -> tuple[Path, Path]:
        timeline = directory / "review.json"
        criteria = directory / "criteria.json"
        timeline.write_text(json.dumps({
            "format": "toolbox-watch-review/v1",
            "evidence_timeline": [
                {"kind": "transcript", "start_seconds": 2, "end_seconds": 3, "text": "The approved material is visible."},
                {"kind": "frame", "timestamp_seconds": 4, "ocr_text": "PLACEHOLDER TEXTURE"},
            ],
        }), encoding="utf-8")
        criteria.write_text(json.dumps({
            "format": "toolbox-asset-review-criteria/v1",
            "criteria": [
                {"id": "material", "required_terms": ["approved", "material"]},
                {"id": "texture", "forbidden_terms": ["placeholder", "texture"]},
                {"id": "topology", "required_terms": ["clean", "topology"]},
            ],
        }), encoding="utf-8")
        return timeline, criteria

    def test_assessment_is_evidence_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            assessment = assess_timeline(*self._inputs(Path(temporary)))
        self.assertEqual(assessment["overall_status"], "FAIL")
        self.assertEqual([finding["status"] for finding in assessment["findings"]], ["PASS", "FAIL", "NEEDS_HUMAN_REVIEW"])
        self.assertTrue(assessment["findings"][0]["citations"])

    def test_assessment_write_preserves_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            timeline, criteria = self._inputs(directory)
            original = timeline.read_text(encoding="utf-8")
            result = assess_timeline(timeline, criteria)
            output = write_assessment(result, timeline, directory / "assessment.json")
            self.assertEqual(timeline.read_text(encoding="utf-8"), original)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["format"], "toolbox-asset-review/v1")

    def test_rejects_duplicate_criterion_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            timeline, criteria = self._inputs(directory)
            criteria.write_text(json.dumps({
                "format": "toolbox-asset-review-criteria/v1",
                "criteria": [{"id": "same", "required_terms": ["a"]}, {"id": "same", "required_terms": ["b"]}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(AssetReviewError, "duplicate"):
                assess_timeline(timeline, criteria)
