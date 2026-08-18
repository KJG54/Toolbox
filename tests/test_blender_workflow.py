from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from toolbox.blender_workflow import BlenderWorkflowError, conversion_command


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
