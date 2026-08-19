from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from toolbox.semantic_vision import MODEL_REVISION, SemanticVisionError, describe_image


class SemanticVisionTests(unittest.TestCase):
    def test_invalid_task_fails_before_loading_a_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "fixture.png"
            Image.new("RGB", (2, 2), "red").save(source)
            with self.assertRaisesRegex(SemanticVisionError, "Unsupported semantic vision task"):
                describe_image(source, task="unsupported")

    def test_model_revision_is_pinned(self) -> None:
        self.assertEqual(len(MODEL_REVISION), 40)
        self.assertTrue(all(character in "0123456789abcdef" for character in MODEL_REVISION))
