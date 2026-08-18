from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from toolbox.watch_review import build_timeline, run_watch_review


class WatchReviewTests(unittest.TestCase):
    def test_timeline_is_versioned_and_time_ordered(self) -> None:
        frame = SimpleNamespace(timestamp_seconds=3.0, path=Path("frame.jpg"), scene_id=2, reason="scene-start", ocr_text="Save")
        perception = SimpleNamespace(engine="scene", scene_count=1, candidate_count=3, deduped_count=2, frames=[frame])
        transcript = SimpleNamespace(source="captions", segments=[SimpleNamespace(start=1.0, end=2.0, text="Open settings", speaker=None)])
        result = SimpleNamespace(
            perception=perception,
            transcript=transcript,
            metadata=SimpleNamespace(duration_seconds=10.0, width=320, height=180, fps=10.0, codec="h264", has_audio=True, size_bytes=5),
            acquisition=SimpleNamespace(source="input.mp4", kind="local", acquirer="local", from_cache=False, video_path=Path("input.mp4")),
        )
        timeline = build_timeline(result, source_asset="input.mp4", pipeline={"local_only": True})
        self.assertEqual(timeline["format"], "toolbox-watch-review/v1")
        self.assertEqual([item["kind"] for item in timeline["evidence_timeline"]], ["transcript", "frame"])
        self.assertEqual(timeline["perception"]["frames"][0]["ocr_text"], "Save")

    def test_review_uses_component_and_blocks_download_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "input.mp4"
            output = directory / "review.json"
            source.write_bytes(b"fixture")
            payload = {"format": "toolbox-watch-review/v1", "pipeline": {"normalization": None}}
            completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
            with patch("toolbox.watch_review.subprocess.run", return_value=completed) as run:
                result = run_watch_review(source, output, max_frames=4, local_whisper=True, whisper_model="tiny")
            self.assertTrue(output.is_file())
            self.assertEqual(result["timeline"]["format"], "toolbox-watch-review/v1")
            self.assertEqual(source.read_bytes(), b"fixture")
            environment = run.call_args.kwargs["env"]
            self.assertEqual(environment["WATCHSKILL_CLOUD_STT_ENABLED"], "false")
            self.assertEqual(environment["HF_HUB_OFFLINE"], "1")
            self.assertIn("watch_runner.py", run.call_args.args[0][1])
            self.assertIn("--whisper-model", run.call_args.args[0])
