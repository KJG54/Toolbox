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

    def test_mesh_validation_welds_duplicate_glb_seam_vertices_for_topology(self) -> None:
        try:
            import trimesh
        except ImportError:
            self.skipTest("Trimesh is not installed")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "seamed-cube.glb"
            source.write_bytes(b"fixture")
            coordinates = [
                (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
            ]
            quads = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
            vertices, faces = [], []
            for quad in quads:
                start = len(vertices)
                vertices.extend(coordinates[index] for index in quad)
                faces.extend([(start, start + 1, start + 2), (start, start + 2, start + 3)])
            seamed_cube = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
            with patch.object(trimesh, "load", return_value=seamed_cube):
                result = validate_mesh(source)
            self.assertGreater(result["vertices"], result["topology_vertices"])
            self.assertTrue(result["watertight"])
            self.assertEqual(result["boundary_edges"], 0)
