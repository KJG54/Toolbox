from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from toolbox.visual_evidence import VisualEvidenceError, compare_images, inspect_image


class VisualEvidenceTests(unittest.TestCase):
    def test_inspect_returns_component_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "image.png"
            image.write_bytes(b"fixture")
            payload = {"format": "toolbox-visual-evidence/v1", "mode": "inspect", "execution": "local_only"}
            completed = CompletedProcess([], 0, json.dumps(payload), "")
            with patch("toolbox.visual_evidence.subprocess.run", return_value=completed):
                self.assertEqual(inspect_image(image)["mode"], "inspect")

    def test_compare_rejects_non_image_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.txt"
            source.write_text("fixture", encoding="utf-8")
            with self.assertRaisesRegex(VisualEvidenceError, "Unsupported image"):
                compare_images(source, source)
