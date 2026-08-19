from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from toolbox.duplicate_finder import find_duplicates
from toolbox.texture_profiles import export_texture_profile
from toolbox.watch_exports import export_chapters, export_subtitles


class PolishWorkflowTests(unittest.TestCase):
    def test_duplicate_finder_reports_exact_local_files_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "one.txt").write_text("same", encoding="utf-8")
            (root / "two.txt").write_text("same", encoding="utf-8")
            report = find_duplicates(root)
            self.assertEqual(report["exact_duplicates"][0]["paths"], ["one.txt", "two.txt"])

    def test_texture_profile_writes_a_distinct_derivative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, output = root / "source.png", root / "mobile.webp"
            Image.new("RGBA", (16, 8), "red").save(source)
            result = export_texture_profile(source, output, profile="mobile")
            self.assertTrue(output.is_file())
            self.assertEqual(result["size"], [16, 8])

    def test_watch_exports_use_saved_timeline_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            timeline = root / "review.json"
            timeline.write_text(json.dumps({"format":"toolbox-watch-review/v1","metadata":{"duration_seconds":5},"transcript":{"segments":[{"start_seconds":0,"end_seconds":1.5,"text":"Hello"}]},"perception":{"frames":[{"timestamp_seconds":0},{"timestamp_seconds":2}]},"evidence_timeline":[]}), encoding="utf-8")
            subtitles = export_subtitles(timeline, root / "review.srt")
            chapters = export_chapters(timeline, root / "review.ffmeta")
            self.assertEqual(subtitles["segments"], 1)
            self.assertEqual(chapters["chapters"], 2)
