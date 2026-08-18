from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from PIL import Image

from toolbox.audio_cleanup import clean_audio
from toolbox.blender_workflow import inspect_game_asset
from toolbox.generation_research import research_generation
from toolbox.image_prep import prepare_image


class ImageAudioAndGenerationTests(unittest.TestCase):
    def test_image_preparation_writes_distinct_resized_derivative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "source.png"
            output = directory / "output.webp"
            Image.new("RGBA", (100, 50), "red").save(source)
            result = prepare_image(source, output, max_width=40)
            self.assertEqual(result["output_size"], (40, 20))
            self.assertTrue(source.is_file())
            self.assertTrue(output.is_file())

    def test_audio_cleanup_creates_distinct_normalized_derivative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "source.wav"
            output = directory / "clean.wav"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                "sine=frequency=440:duration=0.25", str(source),
            ], check=True)
            result = clean_audio(source, output)
            self.assertTrue(result["normalized"])
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)

    def test_game_asset_inspection_marks_missing_readiness_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "asset.blend"
            source.write_bytes(b"fixture")
            payload = {"meshes": [{"name": "Cube", "vertices": 8, "polygons": 6, "triangles": 12, "uv_layers": 0, "materials": 0}], "collider_objects": [], "lod_objects": [], "missing_uv_meshes": ["Cube"]}
            completed = CompletedProcess([], 0, "TOOLBOX_GAME_ASSET_INSPECT=" + json.dumps(payload), "")
            with patch("toolbox.blender_workflow.blender_binary", return_value="blender"), patch("toolbox.blender_workflow.subprocess.run", return_value=completed):
                result = inspect_game_asset(source)
            self.assertEqual(result["status"], "NEEDS_GAME_ASSET_FINISHING")
            self.assertIn("mesh_without_uvs", result["issues"])

    def test_generation_research_is_review_only(self) -> None:
        result = research_generation("music")
        self.assertEqual(result["candidate"], "ACE-Step")
        self.assertEqual(result["external_actions_performed"], [])
        self.assertEqual(result["mutations_performed"], [])
