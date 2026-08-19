from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from toolbox.blender_workflow import BlenderWorkflowError, conversion_command, lod_command, preview_command


class BlenderWorkflowTests(unittest.TestCase):
    def test_conversion_command_preserves_source_and_targets_derivative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "asset.blend"
            output = directory / "asset.glb"
            source.write_bytes(b"fixture")
            with patch("toolbox.blender_workflow.blender_binary", return_value="blender"):
                command = conversion_command(source, output)
            self.assertEqual(command[:3], ["blender", "--background", str(source.resolve())])
            self.assertIn("export_scene.gltf", command[-1])
            self.assertTrue(source.is_file())

    def test_conversion_rejects_source_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "asset.blend"
            source.write_bytes(b"fixture")
            with self.assertRaisesRegex(BlenderWorkflowError, "must differ"):
                conversion_command(source, source)

    def test_preview_command_disables_autoexec_and_bounds_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "asset.blend"
            output = directory / "preview.png"
            source.write_bytes(b"fixture")
            with patch("toolbox.blender_workflow.blender_binary", return_value="blender"):
                command = preview_command(source, output, max_resolution=512)
            self.assertIn("--disable-autoexec", command)
            self.assertIn("bpy.ops.render.render(write_still=True)", command[-1])
            self.assertIn("512", command[-1])

    def test_lod_command_creates_distinct_blend_derivative_with_autoexec_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "asset.blend"
            output = directory / "asset-lod.blend"
            source.write_bytes(b"fixture")
            with patch("toolbox.blender_workflow.blender_binary", return_value="blender"):
                command = lod_command(source, output, ratio=0.5)
            self.assertIn("--disable-autoexec", command)
            self.assertIn("DECIMATE", command[-1])
            self.assertIn(output.name, command[-1])
