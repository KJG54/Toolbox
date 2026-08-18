from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolbox.doctor import doctor_report
from toolbox.provenance import create_sidecar


class DoctorAndProvenanceTests(unittest.TestCase):
    def test_doctor_reports_known_components_without_mutating_runtime(self) -> None:
        report = doctor_report()
        self.assertIn("hardware", report)
        self.assertEqual(report["tools"]["watch-skill"]["status"], "READY")
        self.assertEqual(report["tools"]["watch-skill"]["features"]["perception"], "READY")
        self.assertEqual(report["tools"]["watch-skill"]["features"]["local_whisper"], "READY_TINY_MODEL")
        self.assertEqual(report["tools"]["watch-skill"]["features"]["ocr"], "READY")
        self.assertEqual(report["tools"]["tts-examples"]["status"], "READY")
        self.assertEqual(report["tools"]["local-visual-analysis"]["features"]["pixel_comparison"], "READY")

    def test_provenance_sidecar_preserves_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            asset = Path(temporary) / "key.fbx"
            asset.write_bytes(b"original-asset")
            sidecar = create_sidecar(asset, tools=["blender"], source_assets=[], human_modifications="UV cleanup", commercial_use="requires_review")
            self.assertEqual(asset.read_bytes(), b"original-asset")
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact"], "key.fbx")
            self.assertEqual(payload["created_with"][0]["tool"], "blender")
            with self.assertRaises(FileExistsError):
                create_sidecar(asset, tools=["blender"], source_assets=[], human_modifications="", commercial_use="requires_review")
