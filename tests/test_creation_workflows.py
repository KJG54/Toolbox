from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from PIL import Image

from toolbox.atlas import pack_atlas
from toolbox.blender_workflow import assign_material_maps
from toolbox.generation_research import evaluate_generation, research_generation
from toolbox.video_assembly import assemble_video


class CreationWorkflowTests(unittest.TestCase):
    def test_atlas_packing_creates_png_and_layout_without_changing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sprites = root / "sprites"
            sprites.mkdir()
            source = sprites / "hero.png"
            Image.new("RGBA", (4, 4), "red").save(source)
            Image.new("RGBA", (2, 3), "blue").save(sprites / "coin.png")
            result = pack_atlas(sprites, root / "atlas.png")
            self.assertTrue(Path(result["output"]).is_file())
            self.assertTrue(Path(result["metadata"]).is_file())
            self.assertTrue(source.is_file())

    def test_video_assembly_creates_a_distinct_mp4(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second, output = root / "one.mp4", root / "two.mp4", root / "combined.mp4"
            for target, color in ((first, "red"), (second, "blue")):
                subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=32x32:d=0.1",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=0.1", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(target),
                ], check=True)
            result = assemble_video([first, second], output)
            self.assertTrue(Path(result["output"]).is_file())
            self.assertTrue(first.is_file())

    def test_generation_research_and_evaluation_do_not_install_a_model(self) -> None:
        brief = research_generation("image")
        evaluation = evaluate_generation("music")
        self.assertEqual(brief["candidate"], "FLUX.1 Schnell")
        self.assertFalse(evaluation["installation_performed"])
        self.assertEqual(evaluation["external_actions_performed"], [])

    def test_material_assignment_targets_a_distinct_blend_derivative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, output = root / "asset.blend", root / "asset-textured.blend"
            textures = root / "textures"
            source.write_bytes(b"fixture")
            textures.mkdir()
            Image.new("RGB", (2, 2), "red").save(textures / "crate_BaseColor.png")

            def complete(*args: object, **kwargs: object) -> CompletedProcess[str]:
                output.write_bytes(b"derivative")
                return CompletedProcess([], 0, 'TOOLBOX_MATERIAL_ASSIGN={"applied":[{"material":"Material"}]}', "")

            with patch("toolbox.blender_workflow.blender_binary", return_value="blender"), patch("toolbox.blender_workflow.subprocess.run", side_effect=complete):
                result = assign_material_maps(source, textures, output, material="Material", texture_group="crate")
            self.assertEqual(result["status"], "ASSIGNED")
            self.assertEqual(source.read_bytes(), b"fixture")
