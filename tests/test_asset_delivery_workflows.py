from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from toolbox.asset_catalog import build_catalog, search_catalog
from toolbox.audio_assembly import assemble_audio
from toolbox.blender_workflow import batch_convert_3d
from toolbox.delivery import audit_delivery, package_delivery
from toolbox.provenance import create_sidecar
from toolbox.texture_validation import validate_textures


class AssetDeliveryWorkflowTests(unittest.TestCase):
    def test_catalog_filters_local_filename_tags_and_recorded_commercial_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "assets"
            root.mkdir()
            asset = root / "stone-wall-albedo.png"
            asset.write_bytes(b"fixture")
            create_sidecar(asset, tools=["pillow"], source_assets=[], human_modifications="", commercial_use="allowed")
            catalog = build_catalog(root)
            self.assertEqual(catalog["asset_count"], 1)
            result = search_catalog(root, "stone wall", format_name="png", commercial=True)
            self.assertEqual([item["path"] for item in result["results"]], ["stone-wall-albedo.png"])

    def test_texture_validation_reports_dimensions_alpha_and_map_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGBA", (4, 4), "red").save(root / "crate_BaseColor.png")
            Image.new("RGB", (4, 4), "blue").save(root / "crate_Normal.png")
            report = validate_textures(root)
            self.assertEqual(report["textures"][0]["width"], 4)
            self.assertTrue(report["textures"][0]["has_alpha"])
            self.assertIn("incomplete_material_map_sets", report["issues"])

    def test_audio_assembly_creates_distinct_local_derivative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second, output = root / "one.wav", root / "two.wav", root / "combined.wav"
            for target, frequency in ((first, "440"), (second, "660")):
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency={frequency}:duration=0.1", str(target)], check=True)
            result = assemble_audio([first, second], output)
            self.assertTrue(output.is_file())
            self.assertEqual(len(result["sources"]), 2)
            self.assertTrue(first.is_file())

    def test_batch_3d_conversion_reports_each_source_without_source_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir, output_dir = root / "sources", root / "outputs"
            source_dir.mkdir()
            source = source_dir / "prop.blend"
            source.write_bytes(b"fixture")
            with patch("toolbox.blender_workflow.convert_3d", return_value={"output": str(output_dir / "prop.glb")}) as convert:
                result = batch_convert_3d(source_dir, output_dir, output_format="glb")
            self.assertEqual(result["converted"], 1)
            convert.assert_called_once()
            self.assertEqual(source.read_bytes(), b"fixture")

    def test_delivery_package_requires_provenance_then_packages_audited_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            delivery = root / "delivery"
            delivery.mkdir()
            artifact = delivery / "asset.glb"
            artifact.write_bytes(b"fixture")
            create_sidecar(artifact, tools=["blender"], source_assets=[], human_modifications="", commercial_use="allowed")
            audit = audit_delivery(delivery, required=["asset.glb"])
            self.assertEqual(audit["status"], "READY_FOR_HANDOFF")
            package = package_delivery(delivery, root / "delivery.zip", required=["asset.glb"])
            self.assertTrue(Path(package["output"]).is_file())
