from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolbox.game_creation import asset_manifest, asset_naming_plan, audit_game_prototype, compare_asset_manifests, compare_gameplay_reviews, generate_tone_asset, map_godot_assets, plan_game_3d_remediation, plan_game_audio_package, plan_sprite_animations, plan_watch_highlights, scaffold_game_kit, scaffold_game_release_pack, scaffold_godot_project, scaffold_godot_vertical_slice, write_json
from toolbox.provenance import record_external_generation, sidecar_path


class GameCreationTests(unittest.TestCase):
    def test_naming_plan_and_manifest_comparison_are_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            asset = root / "Stone Wall!.PNG"
            asset.write_bytes(b"before")
            plan = asset_naming_plan(root)
            self.assertEqual(plan["rename_proposals"][0]["proposed_name"], "stone_wall.png")
            before = root / "before.json"
            write_json(asset_manifest(root), before)
            asset.write_bytes(b"after")
            after = root / "after.json"
            write_json(asset_manifest(root), after)
            difference = compare_asset_manifests(before, after)
            self.assertIn("Stone Wall!.PNG", difference["changed"])
            self.assertTrue(asset.is_file())

    def test_procedural_audio_creates_local_wav(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "coin.wav"
            result = generate_tone_asset(output, kind="coin", duration_seconds=0.1)
            self.assertTrue(output.is_file())
            self.assertEqual(result["generation"], "deterministic_procedural_audio_not_ai")

    def test_highlight_plan_only_uses_saved_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            timeline = root / "review.json"
            timeline.write_text(json.dumps({"format":"toolbox-watch-review/v1","evidence_timeline":[],"perception":{"frames":[{"timestamp_seconds":2},{"timestamp_seconds":10}]},"transcript":{"segments":[{"start_seconds":1,"end_seconds":3,"text":"Boss appears"}]}}), encoding="utf-8")
            result = plan_watch_highlights(timeline)
            self.assertEqual(result["clips"][0]["evidence"], "Boss appears")

    def test_scaffold_game_kit_creates_only_requested_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = scaffold_game_kit(Path(temporary) / "kit", name="Prototype")
            self.assertTrue(Path(result["manifest"]).is_file())
            self.assertTrue((Path(result["output"]) / "audio" / "sfx").is_dir())

    def test_godot_scaffold_and_map_do_not_require_an_engine(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "prototype"
            result = scaffold_godot_project(root, name="Prototype")
            texture = root / "assets" / "art" / "hero.png"
            texture.write_bytes(b"fixture")
            mapping = map_godot_assets(root)
            self.assertTrue(Path(result["project_file"]).is_file())
            self.assertEqual(mapping["assets"][0]["resource_path"], "res://assets/art/hero.png")

    def test_sprite_plan_and_gameplay_regression_report_saved_evidence_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            layout = root / "sprites.atlas.json"
            layout.write_text(json.dumps({"format":"toolbox-atlas-layout/v1","atlas":"sprites.png","sprites":[{"name":"run_01.png","x":0,"y":0,"width":4,"height":4},{"name":"run_02.png","x":4,"y":0,"width":4,"height":4}]}), encoding="utf-8")
            plan = plan_sprite_animations(layout)
            self.assertEqual(plan["animations"][0]["name"], "run")
            baseline, candidate = root / "baseline.json", root / "candidate.json"
            baseline.write_text(json.dumps({"format":"toolbox-gameplay-review/v1","findings":[{"id":"jump","status":"OBSERVED"}]}), encoding="utf-8")
            candidate.write_text(json.dumps({"format":"toolbox-gameplay-review/v1","findings":[{"id":"jump","status":"NEEDS_HUMAN_REVIEW"}]}), encoding="utf-8")
            regression = compare_gameplay_reviews(baseline, candidate)
            self.assertEqual(regression["status"], "REGRESSION_DETECTED")

    def test_prototype_handoff_requires_asset_provenance_and_optional_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "prototype"
            scaffold_godot_project(root, name="Prototype")
            asset = root / "assets" / "audio" / "jump.wav"
            asset.write_bytes(b"fixture")
            audit = audit_game_prototype(root, require_build=True)
            self.assertIn("asset_provenance_missing", audit["issues"])
            self.assertIn("build_artifact_missing", audit["issues"])

    def test_external_generation_receipt_and_3d_remediation_plan_are_local(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            asset = Path(temporary) / "generated.glb"
            asset.write_bytes(b"fixture")
            receipt = record_external_generation(asset, provider="Meshy", plan="Free", terms_url="https://example.invalid/terms", output_status="ATTRIBUTION_REQUIRED", prompt_reference="design-7", source_assets=["reference.png"])
            self.assertEqual(receipt, sidecar_path(asset))
            plan = plan_game_3d_remediation(asset)
            self.assertEqual(plan["status"], "READY_FOR_LOCAL_INSPECTION")
            self.assertEqual(asset.read_bytes(), b"fixture")

    def test_audio_plan_and_scaffolds_have_explicit_local_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audio = root / "audio"
            audio.mkdir()
            (audio / "music-loop.wav").write_bytes(b"fixture")
            plan = plan_game_audio_package(audio)
            self.assertEqual(plan["status"], "PROVENANCE_REQUIRED")
            slice_result = scaffold_godot_vertical_slice(root / "slice", name="Slice")
            self.assertTrue(Path(slice_result["player_script"]).is_file())
            self.assertTrue(Path(slice_result["checklist"]).is_file())
            release = scaffold_game_release_pack(root / "release", name="Slice")
            self.assertEqual(release["publication"], "not performed")
            self.assertTrue(Path(release["manifest"]).is_file())
