from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from toolbox.gltfpack_workflow import GltfpackError, optimization_command
from toolbox.mesh_validation import MeshValidationError, validate_mesh


class MeshAndGltfpackTests(unittest.TestCase):
    def test_mesh_validation_reports_missing_optional_runtime_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "fixture.obj"
            source.write_text("v 0 0 0\n", encoding="utf-8")
            with patch("toolbox.mesh_validation.trimesh_available", return_value=False):
                with self.assertRaisesRegex(MeshValidationError, "not installed"):
                    validate_mesh(source)
            self.assertEqual(source.read_text(encoding="utf-8"), "v 0 0 0\n")

    def test_gltfpack_requires_installed_binary_and_never_overwrites_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "fixture.glb"
            source.write_bytes(b"fixture")
            with patch("toolbox.gltfpack_workflow.gltfpack_binary", return_value=None):
                with self.assertRaisesRegex(GltfpackError, "not installed"):
                    optimization_command(source, Path(temporary) / "optimized.glb")
            with self.assertRaisesRegex(GltfpackError, "Output must differ"):
                optimization_command(source, source)
            self.assertEqual(source.read_bytes(), b"fixture")
