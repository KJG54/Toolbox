"""Command-line interface for the local-first Toolbox."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .asset_review import AssetReviewError, assess_timeline, write_assessment
from .asset_catalog import AssetCatalogError, build_catalog, search_catalog, write_catalog
from .atlas import AtlasError, pack_atlas
from .audio_assembly import assemble_audio
from .audio_mixing import mix_audio
from .audio_cleanup import AudioCleanupError, clean_audio
from .asset_discovery import search_asset_sources
from .blender_workflow import BlenderWorkflowError, assign_material_maps, batch_convert_3d, convert_3d, create_lod, create_procedural_prop, handoff_report, inspect_blend, inspect_game_asset, preflight_blend, render_preview, render_turntable
from .capability_research import CapabilityResearchError, research_capability, write_research_brief
from .doctor import doctor_report, detect_hardware, detect_tools
from .delivery import DeliveryError, audit_delivery, package_delivery
from .duplicate_finder import find_duplicates
from .evidence_library import EvidenceLibraryError, search_library
from .gameplay_review import GameplayReviewError, review_gameplay, write_gameplay_review
from .game_creation import GameCreationError, asset_manifest, asset_naming_plan, audit_game_prototype, compare_asset_manifests, compare_gameplay_reviews, engine_readiness, generate_tone_asset, inspect_godot_project, map_godot_assets, plan_game_3d_remediation, plan_game_audio_package, plan_sprite_animations, plan_watch_highlights, scaffold_game_kit, scaffold_game_release_pack, scaffold_godot_project, scaffold_godot_vertical_slice, video_contact_sheet, write_json
from .generation_research import GenerationResearchError, evaluate_generation, research_generation
from .gltfpack_workflow import GltfpackError, optimize_gltf
from .image_prep import ImagePrepError, inspect_image_asset, prepare_image
from .media import MediaError, normalize_media
from .mesh_validation import MeshValidationError, validate_mesh
from .provenance import create_sidecar, record_external_generation, sidecar_path
from .registry import RegistryError, load_registry
from .routing import recommend
from .semantic_vision import SemanticVisionError, describe_image
from .timeline_review import TimelineReviewError, answer_timeline, write_answer
from .tutorial_review import TutorialReviewError, verify_tutorial, write_tutorial_review
from .tts_workflow import TTSWorkflowError, synthesize
from .texture_validation import TextureValidationError, validate_textures
from .texture_profiles import TextureProfileError, export_texture_profile
from .visual_evidence import VisualEvidenceError, compare_images, inspect_image
from .video_assembly import assemble_video
from .watch_review import WatchReviewError, run_watch_review
from .watch_exports import export_chapters, export_subtitles


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="toolbox", description="Local-first agent capability toolbox")
    commands = parser.add_subparsers(dest="command", required=True)
    list_parser = commands.add_parser("list")
    list_parser.add_argument("kind", choices=["capabilities", "tools", "models", "licenses", "workflows"])
    search_parser = commands.add_parser("search")
    search_parser.add_argument("query")
    recommendation = commands.add_parser("recommend")
    recommendation.add_argument("capability")
    recommendation.add_argument("--commercial", action="store_true")
    recommendation.add_argument("--free", dest="free_only", action="store_true")
    recommendation.add_argument("--allow-external", action="store_true")
    recommendation.add_argument("--input-format")
    status = commands.add_parser("status")
    status.add_argument("tool")
    commands.add_parser("doctor")
    commands.add_parser("hardware")
    run = commands.add_parser("run")
    run.add_argument("workflow", choices=["normalize-media", "watch-review"])
    run.add_argument("source", type=Path)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--audio-only", action="store_true")
    run.add_argument("--max-width", type=int, default=1280)
    run.add_argument("--force", action="store_true")
    run.add_argument("--no-provenance", action="store_true")
    run.add_argument("--normalize", action="store_true", help="Create a local MP4 proxy before Watch analysis.")
    run.add_argument("--max-frames", type=int, help="Limit retained evidence frames for watch-review.")
    run.add_argument("--ocr", action="store_true", help="Enable Watch OCR when its local dependency is installed.")
    run.add_argument("--local-whisper", action="store_true", help="Use a cached local Whisper model; model downloads remain blocked.")
    run.add_argument("--whisper-model", help="Cached faster-whisper model name, such as tiny or small.")
    review = commands.add_parser("review", help="Query locally saved Watch evidence timelines.")
    review_commands = review.add_subparsers(dest="review_command", required=True)
    ask_review = review_commands.add_parser("ask")
    ask_review.add_argument("timeline", type=Path)
    ask_review.add_argument("question")
    ask_review.add_argument("--max-evidence", type=int, default=5)
    ask_review.add_argument("--output", type=Path)
    ask_review.add_argument("--force", action="store_true")
    ask_review.add_argument("--no-provenance", action="store_true")
    assess_review = review_commands.add_parser("assess")
    assess_review.add_argument("timeline", type=Path)
    assess_review.add_argument("--criteria", type=Path, required=True)
    assess_review.add_argument("--output", type=Path, required=True)
    assess_review.add_argument("--force", action="store_true")
    assess_review.add_argument("--no-provenance", action="store_true")
    tutorial_review = review_commands.add_parser("tutorial")
    tutorial_review.add_argument("timeline", type=Path)
    tutorial_review.add_argument("--steps", type=Path, required=True)
    tutorial_review.add_argument("--output", type=Path, required=True)
    tutorial_review.add_argument("--force", action="store_true")
    tutorial_review.add_argument("--no-provenance", action="store_true")
    gameplay_review = review_commands.add_parser("gameplay")
    gameplay_review.add_argument("timeline", type=Path)
    gameplay_review.add_argument("--events", type=Path, required=True)
    gameplay_review.add_argument("--output", type=Path, required=True)
    gameplay_review.add_argument("--force", action="store_true")
    gameplay_review.add_argument("--no-provenance", action="store_true")
    subtitles_review = review_commands.add_parser("export-subtitles")
    subtitles_review.add_argument("timeline", type=Path)
    subtitles_review.add_argument("--output", type=Path, required=True)
    subtitles_review.add_argument("--force", action="store_true")
    subtitles_review.add_argument("--no-provenance", action="store_true")
    chapters_review = review_commands.add_parser("export-chapters")
    chapters_review.add_argument("timeline", type=Path)
    chapters_review.add_argument("--output", type=Path, required=True)
    chapters_review.add_argument("--force", action="store_true")
    chapters_review.add_argument("--no-provenance", action="store_true")
    library = commands.add_parser("library", help="Search local Watch evidence across saved timelines.")
    library_commands = library.add_subparsers(dest="library_command", required=True)
    library_search = library_commands.add_parser("search")
    library_search.add_argument("directory", type=Path)
    library_search.add_argument("question")
    library_search.add_argument("--max-results", type=int, default=12)
    library_search.add_argument("--semantic", action="store_true", help="Use the cached local embedding model.")
    blender = commands.add_parser("blender", help="Run guarded local Blender workflows.")
    blender_commands = blender.add_subparsers(dest="blender_command", required=True)
    blender_inspect = blender_commands.add_parser("inspect")
    blender_inspect.add_argument("source", type=Path)
    blender_preflight = blender_commands.add_parser("preflight")
    blender_preflight.add_argument("source", type=Path)
    blender_game_asset = blender_commands.add_parser("game-asset")
    blender_game_asset.add_argument("source", type=Path)
    blender_handoff = blender_commands.add_parser("handoff-report")
    blender_handoff.add_argument("source", type=Path)
    blender_lod = blender_commands.add_parser("create-lod")
    blender_lod.add_argument("source", type=Path)
    blender_lod.add_argument("--output", type=Path, required=True)
    blender_lod.add_argument("--ratio", type=float, required=True)
    blender_lod.add_argument("--force", action="store_true")
    blender_lod.add_argument("--no-provenance", action="store_true")
    blender_batch = blender_commands.add_parser("batch")
    blender_batch.add_argument("source_directory", type=Path)
    blender_batch.add_argument("--output-dir", type=Path, required=True)
    blender_batch.add_argument("--format", choices=["blend", "fbx", "obj", "glb"], required=True)
    blender_batch.add_argument("--preview", action="store_true")
    blender_batch.add_argument("--max-assets", type=int, default=500)
    blender_batch.add_argument("--force", action="store_true")
    blender_batch.add_argument("--no-provenance", action="store_true")
    blender_material = blender_commands.add_parser("assign-material")
    blender_material.add_argument("source", type=Path)
    blender_material.add_argument("--textures", type=Path, required=True)
    blender_material.add_argument("--output", type=Path, required=True)
    blender_material.add_argument("--material")
    blender_material.add_argument("--texture-group")
    blender_material.add_argument("--force", action="store_true")
    blender_material.add_argument("--no-provenance", action="store_true")
    blender_turntable = blender_commands.add_parser("turntable")
    blender_turntable.add_argument("source", type=Path)
    blender_turntable.add_argument("--output-dir", type=Path, required=True)
    blender_turntable.add_argument("--frames", type=int, default=12)
    blender_turntable.add_argument("--resolution", type=int, default=512)
    blender_turntable.add_argument("--force", action="store_true")
    blender_turntable.add_argument("--no-provenance", action="store_true")
    blender_prop = blender_commands.add_parser("procedural-prop")
    blender_prop.add_argument("--kind", choices=["crate", "barrel", "ramp", "platform"], required=True)
    blender_prop.add_argument("--output", type=Path, required=True)
    blender_prop.add_argument("--force", action="store_true")
    blender_prop.add_argument("--no-provenance", action="store_true")
    blender_convert = blender_commands.add_parser("convert")
    blender_convert.add_argument("source", type=Path)
    blender_convert.add_argument("--output", type=Path, required=True)
    blender_convert.add_argument("--force", action="store_true")
    blender_convert.add_argument("--no-provenance", action="store_true")
    blender_preview = blender_commands.add_parser("preview")
    blender_preview.add_argument("source", type=Path)
    blender_preview.add_argument("--output", type=Path, required=True)
    blender_preview.add_argument("--max-resolution", type=int, default=1024)
    blender_preview.add_argument("--force", action="store_true")
    blender_preview.add_argument("--no-provenance", action="store_true")
    visual = commands.add_parser("visual", help="Inspect or compare local images without uploading them.")
    visual_commands = visual.add_subparsers(dest="visual_command", required=True)
    visual_inspect = visual_commands.add_parser("inspect")
    visual_inspect.add_argument("source", type=Path)
    visual_compare = visual_commands.add_parser("compare")
    visual_compare.add_argument("reference", type=Path)
    visual_compare.add_argument("candidate", type=Path)
    vision = commands.add_parser("vision", help="Run an explicitly approved local semantic image model.")
    vision_commands = vision.add_subparsers(dest="vision_command", required=True)
    vision_describe = vision_commands.add_parser("describe")
    vision_describe.add_argument("source", type=Path)
    vision_describe.add_argument("--task", choices=["caption", "detailed-caption", "object-detection"], default="caption")
    image = commands.add_parser("image", help="Prepare non-destructive local image derivatives.")
    image_commands = image.add_subparsers(dest="image_command", required=True)
    image_inspect = image_commands.add_parser("inspect")
    image_inspect.add_argument("source", type=Path)
    image_prepare = image_commands.add_parser("prepare")
    image_prepare.add_argument("source", type=Path)
    image_prepare.add_argument("--output", type=Path, required=True)
    image_prepare.add_argument("--max-width", type=int)
    image_prepare.add_argument("--max-height", type=int)
    image_prepare.add_argument("--allow-upscale", action="store_true")
    image_prepare.add_argument("--force", action="store_true")
    image_prepare.add_argument("--no-provenance", action="store_true")
    audio = commands.add_parser("audio", help="Create guarded local audio cleanup derivatives.")
    audio_commands = audio.add_subparsers(dest="audio_command", required=True)
    audio_clean = audio_commands.add_parser("clean")
    audio_clean.add_argument("source", type=Path)
    audio_clean.add_argument("--output", type=Path, required=True)
    audio_clean.add_argument("--no-normalize", action="store_true")
    audio_clean.add_argument("--start-seconds", type=float)
    audio_clean.add_argument("--end-seconds", type=float)
    audio_clean.add_argument("--force", action="store_true")
    audio_clean.add_argument("--no-provenance", action="store_true")
    audio_assemble = audio_commands.add_parser("assemble")
    audio_assemble.add_argument("sources", nargs="+", type=Path)
    audio_assemble.add_argument("--output", type=Path, required=True)
    audio_assemble.add_argument("--no-normalize", action="store_true")
    audio_assemble.add_argument("--force", action="store_true")
    audio_assemble.add_argument("--no-provenance", action="store_true")
    audio_mix = audio_commands.add_parser("mix")
    audio_mix.add_argument("--narration", type=Path, required=True)
    audio_mix.add_argument("--bed", type=Path, required=True)
    audio_mix.add_argument("--output", type=Path, required=True)
    audio_mix.add_argument("--narration-gain-db", type=float, default=0)
    audio_mix.add_argument("--bed-gain-db", type=float, default=-18)
    audio_mix.add_argument("--fade-seconds", type=float, default=0.5)
    audio_mix.add_argument("--no-ducking", action="store_true")
    audio_mix.add_argument("--force", action="store_true")
    audio_mix.add_argument("--no-provenance", action="store_true")
    audio_procedural = audio_commands.add_parser("procedural")
    audio_procedural.add_argument("--kind", choices=["coin", "jump", "hit", "laser", "ambient", "loop"], required=True)
    audio_procedural.add_argument("--output", type=Path, required=True)
    audio_procedural.add_argument("--duration", type=float, default=1.0)
    audio_procedural.add_argument("--seed", type=int, default=1)
    audio_procedural.add_argument("--force", action="store_true")
    audio_procedural.add_argument("--no-provenance", action="store_true")
    catalog = commands.add_parser("catalog", help="Index and search downloaded local assets.")
    catalog_commands = catalog.add_subparsers(dest="catalog_command", required=True)
    catalog_index = catalog_commands.add_parser("index")
    catalog_index.add_argument("directory", type=Path)
    catalog_index.add_argument("--max-files", type=int, default=10000)
    catalog_index.add_argument("--output", type=Path)
    catalog_index.add_argument("--force", action="store_true")
    catalog_search = catalog_commands.add_parser("search")
    catalog_search.add_argument("directory", type=Path)
    catalog_search.add_argument("query", nargs="?", default="")
    catalog_search.add_argument("--format")
    catalog_search.add_argument("--tag")
    catalog_search.add_argument("--commercial", action="store_true")
    catalog_search.add_argument("--max-files", type=int, default=10000)
    catalog_duplicates = catalog_commands.add_parser("find-duplicates")
    catalog_duplicates.add_argument("directory", type=Path)
    catalog_duplicates.add_argument("--threshold", type=int, default=4)
    catalog_duplicates.add_argument("--max-files", type=int, default=10000)
    texture = commands.add_parser("texture", help="Validate local texture and material-map readiness.")
    texture_commands = texture.add_subparsers(dest="texture_command", required=True)
    texture_validate = texture_commands.add_parser("validate")
    texture_validate.add_argument("source", type=Path)
    texture_profile = texture_commands.add_parser("export-profile")
    texture_profile.add_argument("source", type=Path)
    texture_profile.add_argument("--profile", choices=["mobile", "desktop", "game-hd", "godot-mobile", "godot-desktop"], required=True)
    texture_profile.add_argument("--output", type=Path, required=True)
    texture_profile.add_argument("--force", action="store_true")
    texture_profile.add_argument("--no-provenance", action="store_true")
    atlas = commands.add_parser("atlas", help="Pack local sprites and textures into an atlas derivative.")
    atlas_commands = atlas.add_subparsers(dest="atlas_command", required=True)
    atlas_pack = atlas_commands.add_parser("pack")
    atlas_pack.add_argument("source_directory", type=Path)
    atlas_pack.add_argument("--output", type=Path, required=True)
    atlas_pack.add_argument("--padding", type=int, default=2)
    atlas_pack.add_argument("--max-width", type=int, default=2048)
    atlas_pack.add_argument("--force", action="store_true")
    atlas_pack.add_argument("--no-provenance", action="store_true")
    video = commands.add_parser("video", help="Assemble local video clips into a derivative.")
    video_commands = video.add_subparsers(dest="video_command", required=True)
    video_assemble = video_commands.add_parser("assemble")
    video_assemble.add_argument("sources", nargs="+", type=Path)
    video_assemble.add_argument("--output", type=Path, required=True)
    video_assemble.add_argument("--force", action="store_true")
    video_assemble.add_argument("--no-provenance", action="store_true")
    video_contact = video_commands.add_parser("contact-sheet")
    video_contact.add_argument("source", type=Path)
    video_contact.add_argument("--output", type=Path, required=True)
    video_contact.add_argument("--columns", type=int, default=4)
    video_contact.add_argument("--frames", type=int, default=12)
    video_contact.add_argument("--force", action="store_true")
    video_contact.add_argument("--no-provenance", action="store_true")
    game = commands.add_parser("game", help="Plan and create bounded, local game-production assets.")
    game_commands = game.add_subparsers(dest="game_command", required=True)
    game_naming = game_commands.add_parser("naming-plan")
    game_naming.add_argument("directory", type=Path)
    game_naming.add_argument("--max-files", type=int, default=10000)
    game_manifest = game_commands.add_parser("manifest")
    game_manifest.add_argument("directory", type=Path)
    game_manifest.add_argument("--output", type=Path, required=True)
    game_manifest.add_argument("--max-files", type=int, default=10000)
    game_manifest.add_argument("--force", action="store_true")
    game_compare = game_commands.add_parser("compare-manifests")
    game_compare.add_argument("before", type=Path)
    game_compare.add_argument("after", type=Path)
    game_highlights = game_commands.add_parser("plan-highlights")
    game_highlights.add_argument("timeline", type=Path)
    game_highlights.add_argument("--output", type=Path, required=True)
    game_highlights.add_argument("--max-clips", type=int, default=8)
    game_highlights.add_argument("--force", action="store_true")
    game_commands.add_parser("engine-readiness")
    game_kit = game_commands.add_parser("scaffold-kit")
    game_kit.add_argument("--output", type=Path, required=True)
    game_kit.add_argument("--name", required=True)
    game_kit.add_argument("--force", action="store_true")
    godot_scaffold = game_commands.add_parser("godot-scaffold")
    godot_scaffold.add_argument("--output", type=Path, required=True)
    godot_scaffold.add_argument("--name", required=True)
    godot_scaffold.add_argument("--force", action="store_true")
    godot_inspect = game_commands.add_parser("godot-inspect")
    godot_inspect.add_argument("project", type=Path)
    godot_map = game_commands.add_parser("godot-import-map")
    godot_map.add_argument("project", type=Path)
    sprite_plan = game_commands.add_parser("sprite-animation-plan")
    sprite_plan.add_argument("layout", type=Path)
    sprite_plan.add_argument("--separator", default="_")
    sprite_plan.add_argument("--output", type=Path, required=True)
    sprite_plan.add_argument("--force", action="store_true")
    gameplay_regression = game_commands.add_parser("compare-gameplay")
    gameplay_regression.add_argument("baseline", type=Path)
    gameplay_regression.add_argument("candidate", type=Path)
    prototype_handoff = game_commands.add_parser("prototype-handoff")
    prototype_handoff.add_argument("project", type=Path)
    prototype_handoff.add_argument("--require-build", action="store_true")
    game_3d_plan = game_commands.add_parser("3d-remediation-plan")
    game_3d_plan.add_argument("asset", type=Path)
    game_3d_plan.add_argument("--output", type=Path, required=True)
    game_3d_plan.add_argument("--force", action="store_true")
    game_audio_plan = game_commands.add_parser("audio-package-plan")
    game_audio_plan.add_argument("directory", type=Path)
    game_audio_plan.add_argument("--output", type=Path, required=True)
    game_audio_plan.add_argument("--max-files", type=int, default=10000)
    game_audio_plan.add_argument("--force", action="store_true")
    vertical_slice = game_commands.add_parser("godot-vertical-slice")
    vertical_slice.add_argument("--output", type=Path, required=True)
    vertical_slice.add_argument("--name", required=True)
    vertical_slice.add_argument("--force", action="store_true")
    release_pack = game_commands.add_parser("release-pack")
    release_pack.add_argument("--output", type=Path, required=True)
    release_pack.add_argument("--name", required=True)
    release_pack.add_argument("--force", action="store_true")
    mesh = commands.add_parser("mesh", help="Run guarded local mesh validation through Trimesh.")
    mesh_commands = mesh.add_subparsers(dest="mesh_command", required=True)
    mesh_validate = mesh_commands.add_parser("validate")
    mesh_validate.add_argument("source", type=Path)
    mesh_validate.add_argument("--output", type=Path)
    mesh_validate.add_argument("--force", action="store_true")
    gltfpack = commands.add_parser("gltfpack", help="Create a separate optimized GLB with local gltfpack.")
    gltfpack.add_argument("source", type=Path)
    gltfpack.add_argument("--output", type=Path, required=True)
    gltfpack.add_argument("--texture-compression", action="store_true")
    gltfpack.add_argument("--force", action="store_true")
    gltfpack.add_argument("--no-provenance", action="store_true")
    delivery = commands.add_parser("delivery", help="Audit and package a local handoff directory.")
    delivery_commands = delivery.add_subparsers(dest="delivery_command", required=True)
    delivery_audit = delivery_commands.add_parser("audit")
    delivery_audit.add_argument("directory", type=Path)
    delivery_audit.add_argument("--require", action="append", default=[])
    delivery_audit.add_argument("--allow-missing-provenance", action="store_true")
    delivery_package = delivery_commands.add_parser("package")
    delivery_package.add_argument("directory", type=Path)
    delivery_package.add_argument("--output", type=Path, required=True)
    delivery_package.add_argument("--require", action="append", default=[])
    delivery_package.add_argument("--allow-missing-provenance", action="store_true")
    delivery_package.add_argument("--force", action="store_true")
    delivery_package.add_argument("--no-provenance", action="store_true")
    research = commands.add_parser("research", help="Create review-only capability and asset discovery briefs.")
    research_commands = research.add_subparsers(dest="research_command", required=True)
    research_gap = research_commands.add_parser("gap")
    research_gap.add_argument("capability")
    research_gap.add_argument("--commercial", action="store_true")
    research_gap.add_argument("--free", action="store_true")
    research_gap.add_argument("--input")
    research_gap.add_argument("--output", type=Path)
    research_gap.add_argument("--force", action="store_true")
    asset_search = research_commands.add_parser("assets")
    asset_search.add_argument("query")
    asset_search.add_argument("--kind")
    asset_search.add_argument("--commercial", action="store_true")
    generation_research = research_commands.add_parser("generation")
    generation_research.add_argument("kind", choices=["image", "music", "sfx"])
    generation_evaluation = research_commands.add_parser("evaluate-generation")
    generation_evaluation.add_argument("kind", choices=["image", "music", "sfx"])
    tts = commands.add_parser("tts", help="Run guarded local Windows speech synthesis.")
    tts_commands = tts.add_subparsers(dest="tts_command", required=True)
    tts_speak = tts_commands.add_parser("speak")
    tts_speak.add_argument("text")
    tts_speak.add_argument("--output", type=Path, required=True)
    tts_speak.add_argument("--voice")
    tts_speak.add_argument("--force", action="store_true")
    tts_speak.add_argument("--no-provenance", action="store_true")
    provenance = commands.add_parser("provenance")
    provenance_commands = provenance.add_subparsers(dest="provenance_command", required=True)
    show = provenance_commands.add_parser("show")
    show.add_argument("asset", type=Path)
    create = provenance_commands.add_parser("create")
    create.add_argument("asset", type=Path)
    create.add_argument("--tool", dest="tools", action="append", required=True)
    create.add_argument("--source-asset", dest="source_assets", action="append", default=[])
    create.add_argument("--human-modifications", default="")
    create.add_argument("--commercial-use", default="requires_review")
    create.add_argument("--force", action="store_true")
    external = provenance_commands.add_parser("external", help="Record an already-downloaded external generation without contacting its provider.")
    external.add_argument("asset", type=Path)
    external.add_argument("--provider", required=True)
    external.add_argument("--plan", required=True)
    external.add_argument("--terms-url", required=True)
    external.add_argument("--output-status", choices=["DRAFT_ONLY", "PERSONAL_ONLY", "ATTRIBUTION_REQUIRED", "RECHECK_TERMS", "RELEASE_APPROVED"], required=True)
    external.add_argument("--prompt-reference", default="")
    external.add_argument("--source", action="append", default=[])
    external.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            _print(doctor_report())
            return
        if args.command == "hardware":
            _print(detect_hardware())
            return
        if args.command == "run":
            if args.workflow == "normalize-media":
                result = normalize_media(
                    args.source,
                    args.output,
                    audio_only=args.audio_only,
                    max_width=args.max_width,
                    overwrite=args.force,
                )
                tools = ["ffmpeg"]
                note = "Toolbox local media normalization"
            else:
                result = run_watch_review(
                    args.source,
                    args.output,
                    normalize=args.normalize,
                    max_width=args.max_width,
                    max_frames=args.max_frames,
                    ocr=args.ocr,
                    local_whisper=args.local_whisper,
                    whisper_model=args.whisper_model,
                    overwrite=args.force,
                )
                tools = ["watch-skill", *(["ffmpeg"] if args.normalize else [])]
                note = "Toolbox local Watch evidence review"
            if not args.no_provenance:
                result["provenance"] = str(
                    create_sidecar(
                        args.output,
                        tools=tools,
                        source_assets=[str(args.source.resolve())],
                        human_modifications=note,
                        commercial_use="requires_review",
                        force=args.force,
                    )
                )
            _print(result)
            return
        if args.command == "review":
            if args.review_command == "ask":
                result = answer_timeline(args.timeline, args.question, max_evidence=args.max_evidence)
                if args.output:
                    destination = write_answer(result, args.timeline, args.output, overwrite=args.force)
                    result["output"] = str(destination)
                    if not args.no_provenance:
                        result["provenance_sidecar"] = str(
                            create_sidecar(
                                args.output,
                                tools=["watch-skill", "toolbox-local-timeline-review"],
                                source_assets=[str(args.timeline.resolve())],
                                human_modifications="Toolbox local question-directed timeline review",
                                commercial_use="requires_review",
                                force=args.force,
                            )
                        )
            elif args.review_command == "assess":
                result = assess_timeline(args.timeline, args.criteria)
                destination = write_assessment(result, args.timeline, args.output, overwrite=args.force)
                result["output"] = str(destination)
                if not args.no_provenance:
                    result["provenance_sidecar"] = str(
                        create_sidecar(
                            args.output,
                            tools=["watch-skill", "toolbox-local-asset-review"],
                            source_assets=[str(args.timeline.resolve()), str(args.criteria.resolve())],
                            human_modifications="Toolbox local evidence-based asset assessment",
                            commercial_use="requires_review",
                            force=args.force,
                        )
                    )
            elif args.review_command == "tutorial":
                result = verify_tutorial(args.timeline, args.steps)
                destination = write_tutorial_review(result, args.timeline, args.output, overwrite=args.force)
                result["output"] = str(destination)
                if not args.no_provenance:
                    result["provenance_sidecar"] = str(
                        create_sidecar(
                            args.output,
                            tools=["watch-skill", "toolbox-local-ui-tutorial-review"],
                            source_assets=[str(args.timeline.resolve()), str(args.steps.resolve())],
                            human_modifications="Toolbox local software and UI tutorial verification",
                            commercial_use="requires_review",
                            force=args.force,
                        )
                    )
            elif args.review_command == "gameplay":
                result = review_gameplay(args.timeline, args.events)
                destination = write_gameplay_review(result, args.timeline, args.output, overwrite=args.force)
                result["output"] = str(destination)
                if not args.no_provenance:
                    result["provenance_sidecar"] = str(
                        create_sidecar(
                            args.output,
                            tools=["watch-skill", "toolbox-local-gameplay-review"],
                            source_assets=[str(args.timeline.resolve()), str(args.events.resolve())],
                            human_modifications="Toolbox local gameplay evidence review",
                            commercial_use="requires_review",
                            force=args.force,
                        )
                    )
            elif args.review_command == "export-subtitles":
                result = export_subtitles(args.timeline, args.output, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["watch-skill"], source_assets=[str(args.timeline.resolve())],
                        human_modifications="Toolbox local Watch subtitle export", commercial_use="requires_review", force=args.force,
                    ))
            else:
                result = export_chapters(args.timeline, args.output, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["watch-skill"], source_assets=[str(args.timeline.resolve())],
                        human_modifications="Toolbox local Watch chapter export", commercial_use="requires_review", force=args.force,
                    ))
            _print(result)
            return
        if args.command == "library":
            _print(search_library(args.directory, args.question, max_results=args.max_results, semantic=args.semantic))
            return
        if args.command == "blender":
            if args.blender_command == "inspect":
                _print(inspect_blend(args.source))
            elif args.blender_command == "preflight":
                _print(preflight_blend(args.source))
            elif args.blender_command == "game-asset":
                _print(inspect_game_asset(args.source))
            elif args.blender_command == "handoff-report":
                _print(handoff_report(args.source))
            elif args.blender_command == "create-lod":
                result = create_lod(args.source, args.output, ratio=args.ratio, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["blender"], source_assets=[str(args.source.resolve())],
                        human_modifications=f"Toolbox local decimate LOD derivative at ratio {args.ratio}", commercial_use="allowed", force=args.force,
                    ))
                _print(result)
            elif args.blender_command == "batch":
                result = batch_convert_3d(
                    args.source_directory, args.output_dir, output_format=args.format, previews=args.preview,
                    overwrite=args.force, max_assets=args.max_assets,
                )
                if not args.no_provenance:
                    for item in result["results"]:
                        if item["status"] == "CONVERTED":
                            item["provenance"] = str(create_sidecar(
                                Path(item["output"]), tools=["blender"], source_assets=[item["source"]],
                                human_modifications="Toolbox local batch 3D conversion", commercial_use="allowed", force=args.force,
                            ))
                            if "preview" in item:
                                item["preview"]["provenance"] = str(create_sidecar(
                                    Path(item["preview"]["output"]), tools=["blender"], source_assets=[item["source"]],
                                    human_modifications="Toolbox local batch Blender preview", commercial_use="allowed", force=args.force,
                                ))
                _print(result)
            elif args.blender_command == "assign-material":
                result = assign_material_maps(
                    args.source, args.textures, args.output, material=args.material,
                    texture_group=args.texture_group, overwrite=args.force,
                )
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["blender"], source_assets=[str(args.source.resolve()), str(args.textures.resolve())],
                        human_modifications="Toolbox local material-map assignment", commercial_use="requires_review", force=args.force,
                    ))
                _print(result)
            elif args.blender_command == "turntable":
                result = render_turntable(args.source, args.output_dir, frames=args.frames, resolution=args.resolution, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = [str(create_sidecar(
                        Path(frame), tools=["blender"], source_assets=[str(args.source.resolve())],
                        human_modifications="Toolbox local Blender turntable frame", commercial_use="allowed", force=args.force,
                    )) for frame in result["frames"]]
                _print(result)
            elif args.blender_command == "procedural-prop":
                result = create_procedural_prop(args.output, kind=args.kind, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["blender"], source_assets=[],
                        human_modifications=f"Toolbox local procedural {args.kind} geometry", commercial_use="allowed", force=args.force,
                    ))
                _print(result)
            elif args.blender_command == "preview":
                result = render_preview(args.source, args.output, max_resolution=args.max_resolution, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["blender"], source_assets=[str(args.source.resolve())],
                        human_modifications="Toolbox local Blender preview render", commercial_use="allowed", force=args.force,
                    ))
                _print(result)
            else:
                result = convert_3d(args.source, args.output, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["blender"], source_assets=[str(args.source.resolve())],
                        human_modifications="Toolbox local Blender conversion", commercial_use="allowed", force=args.force,
                    ))
                _print(result)
            return
        if args.command == "visual":
            _print(inspect_image(args.source) if args.visual_command == "inspect" else compare_images(args.reference, args.candidate))
            return
        if args.command == "vision":
            _print(describe_image(args.source, task=args.task))
            return
        if args.command == "image":
            if args.image_command == "inspect":
                _print(inspect_image_asset(args.source))
            else:
                result = prepare_image(
                    args.source, args.output, max_width=args.max_width, max_height=args.max_height,
                    allow_upscale=args.allow_upscale, overwrite=args.force,
                )
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["pillow-image-prep"], source_assets=[str(args.source.resolve())],
                        human_modifications="Toolbox local image preparation", commercial_use="allowed", force=args.force,
                    ))
                _print(result)
            return
        if args.command == "audio":
            if args.audio_command == "procedural":
                result = generate_tone_asset(args.output, kind=args.kind, duration_seconds=args.duration, seed=args.seed, overwrite=args.force)
                sources = []
                modification = f"Toolbox local deterministic procedural {args.kind} audio"
                provenance_tool = "toolbox-procedural-audio"
            elif args.audio_command == "assemble":
                result = assemble_audio(args.sources, args.output, normalize=not args.no_normalize, overwrite=args.force)
                sources = [str(source.resolve()) for source in args.sources]
                modification = "Toolbox local ordered audio assembly"
                provenance_tool = "ffmpeg"
            elif args.audio_command == "mix":
                result = mix_audio(args.narration, args.bed, args.output, narration_gain_db=args.narration_gain_db, bed_gain_db=args.bed_gain_db, fade_seconds=args.fade_seconds, ducking=not args.no_ducking, overwrite=args.force)
                sources = [str(args.narration.resolve()), str(args.bed.resolve())]
                modification = "Toolbox local narration and music-bed mix"
                provenance_tool = "ffmpeg"
            else:
                result = clean_audio(
                    args.source, args.output, normalize=not args.no_normalize, start_seconds=args.start_seconds,
                    end_seconds=args.end_seconds, overwrite=args.force,
                )
                sources = [str(args.source.resolve())]
                modification = "Toolbox local audio cleanup"
                provenance_tool = "ffmpeg"
            if not args.no_provenance:
                result["provenance"] = str(create_sidecar(
                    args.output, tools=[provenance_tool], source_assets=sources,
                    human_modifications=modification, commercial_use="allowed" if args.audio_command == "procedural" else "requires_review", force=args.force,
                ))
            _print(result)
            return
        if args.command == "catalog":
            if args.catalog_command == "index":
                result = build_catalog(args.directory, max_files=args.max_files)
                if args.output:
                    result["output"] = str(write_catalog(result, args.output, overwrite=args.force))
            elif args.catalog_command == "search":
                result = search_catalog(
                    args.directory, args.query, format_name=args.format, tag=args.tag,
                    commercial=args.commercial, max_files=args.max_files,
                )
            else:
                result = find_duplicates(args.directory, threshold=args.threshold, max_files=args.max_files)
            _print(result)
            return
        if args.command == "texture":
            if args.texture_command == "validate":
                _print(validate_textures(args.source))
            else:
                result = export_texture_profile(args.source, args.output, profile=args.profile, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["pillow-image-prep"], source_assets=[str(args.source.resolve())],
                        human_modifications=f"Toolbox {args.profile} game texture profile", commercial_use="allowed", force=args.force,
                    ))
                _print(result)
            return
        if args.command == "atlas":
            result = pack_atlas(args.source_directory, args.output, padding=args.padding, max_width=args.max_width, overwrite=args.force)
            if not args.no_provenance:
                result["provenance"] = str(create_sidecar(
                    args.output, tools=["pillow-image-prep"], source_assets=[str(args.source_directory.resolve())],
                    human_modifications="Toolbox local sprite and texture atlas packing", commercial_use="requires_review", force=args.force,
                ))
            _print(result)
            return
        if args.command == "video":
            if args.video_command == "contact-sheet":
                result = video_contact_sheet(args.source, args.output, columns=args.columns, frames=args.frames, overwrite=args.force)
                source_assets = [str(args.source.resolve())]
                modification = "Toolbox local video contact-sheet generation"
            else:
                result = assemble_video(args.sources, args.output, overwrite=args.force)
                source_assets = [str(source.resolve()) for source in args.sources]
                modification = "Toolbox local ordered video assembly"
            if not args.no_provenance:
                result["provenance"] = str(create_sidecar(
                    args.output, tools=["ffmpeg"], source_assets=source_assets,
                    human_modifications=modification, commercial_use="requires_review", force=args.force,
                ))
            _print(result)
            return
        if args.command == "game":
            if args.game_command == "naming-plan":
                result = asset_naming_plan(args.directory, max_files=args.max_files)
            elif args.game_command == "manifest":
                result = asset_manifest(args.directory, max_files=args.max_files)
                result["output"] = str(write_json(result, args.output, overwrite=args.force))
            elif args.game_command == "compare-manifests":
                result = compare_asset_manifests(args.before, args.after)
            elif args.game_command == "plan-highlights":
                result = plan_watch_highlights(args.timeline, max_clips=args.max_clips)
                result["output"] = str(write_json(result, args.output, overwrite=args.force))
            elif args.game_command == "engine-readiness":
                result = engine_readiness()
            elif args.game_command == "scaffold-kit":
                result = scaffold_game_kit(args.output, name=args.name, overwrite=args.force)
            elif args.game_command == "godot-scaffold":
                result = scaffold_godot_project(args.output, name=args.name, overwrite=args.force)
            elif args.game_command == "godot-inspect":
                result = inspect_godot_project(args.project)
            elif args.game_command == "godot-import-map":
                result = map_godot_assets(args.project)
            elif args.game_command == "sprite-animation-plan":
                result = plan_sprite_animations(args.layout, separator=args.separator)
                result["output"] = str(write_json(result, args.output, overwrite=args.force))
            elif args.game_command == "compare-gameplay":
                result = compare_gameplay_reviews(args.baseline, args.candidate)
            elif args.game_command == "prototype-handoff":
                result = audit_game_prototype(args.project, require_build=args.require_build)
            elif args.game_command == "3d-remediation-plan":
                result = plan_game_3d_remediation(args.asset)
                result["output"] = str(write_json(result, args.output, overwrite=args.force))
            elif args.game_command == "audio-package-plan":
                result = plan_game_audio_package(args.directory, max_files=args.max_files)
                result["output"] = str(write_json(result, args.output, overwrite=args.force))
            elif args.game_command == "godot-vertical-slice":
                result = scaffold_godot_vertical_slice(args.output, name=args.name, overwrite=args.force)
            else:
                result = scaffold_game_release_pack(args.output, name=args.name, overwrite=args.force)
            _print(result)
            return
        if args.command == "mesh":
            result = validate_mesh(args.source)
            if args.output:
                result["output"] = str(write_json(result, args.output, overwrite=args.force))
            _print(result)
            return
        if args.command == "gltfpack":
            result = optimize_gltf(args.source, args.output, texture_compression=args.texture_compression, overwrite=args.force)
            if not args.no_provenance:
                result["provenance"] = str(create_sidecar(args.output, tools=["gltfpack", "meshoptimizer"], source_assets=[str(args.source.resolve())], human_modifications="Toolbox local glTF optimization derivative", commercial_use="requires_review", force=args.force))
            _print(result)
            return
        if args.command == "delivery":
            require_provenance = not args.allow_missing_provenance
            if args.delivery_command == "audit":
                _print(audit_delivery(args.directory, required=args.require, require_provenance=require_provenance))
            else:
                result = package_delivery(
                    args.directory, args.output, required=args.require,
                    require_provenance=require_provenance, overwrite=args.force,
                )
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["toolbox-delivery-package"], source_assets=[str(args.directory.resolve())],
                        human_modifications="Toolbox local delivery audit and ZIP package", commercial_use="requires_review", force=args.force,
                    ))
                _print(result)
            return
        if args.command == "research":
            if args.research_command == "gap":
                result = research_capability(args.capability, commercial=args.commercial, free_only=args.free, input_format=args.input)
                if args.output:
                    result["output"] = str(write_research_brief(result, args.output, overwrite=args.force))
            elif args.research_command == "assets":
                result = search_asset_sources(args.query, kind=args.kind, commercial=args.commercial)
            elif args.research_command == "generation":
                result = research_generation(args.kind)
            else:
                result = evaluate_generation(args.kind)
            _print(result)
            return
        if args.command == "tts":
            result = synthesize(args.text, args.output, voice=args.voice, overwrite=args.force)
            if not args.no_provenance:
                result["provenance"] = str(create_sidecar(
                    args.output, tools=["windows-sapi-tts"], source_assets=[],
                    human_modifications="Toolbox local Windows text-to-speech synthesis", commercial_use="requires_review", force=args.force,
                ))
            _print(result)
            return
        if args.command == "provenance":
            path = sidecar_path(args.asset)
            if args.provenance_command == "show":
                _print(json.loads(path.read_text(encoding="utf-8")))
            elif args.provenance_command == "create":
                _print({"sidecar": str(create_sidecar(args.asset, tools=args.tools, source_assets=args.source_assets, human_modifications=args.human_modifications, commercial_use=args.commercial_use, force=args.force))})
            else:
                result = record_external_generation(args.asset, provider=args.provider, plan=args.plan, terms_url=args.terms_url, output_status=args.output_status, prompt_reference=args.prompt_reference, source_assets=args.source, force=args.force)
                _print({"sidecar": str(result), "execution": "local_only_no_external_request"})
            return
        registry = load_registry()
        if args.command == "list":
            _print(registry.records(args.kind))
        elif args.command == "search":
            query = args.query.casefold()
            matches = [record for records in registry.data.values() for record in records if query in json.dumps(record).casefold()]
            _print(matches)
        elif args.command == "recommend":
            _print(recommend(args.capability, commercial=args.commercial, free_only=args.free_only, allow_external=args.allow_external, input_format=args.input_format, registry=registry))
        elif args.command == "status":
            tool = registry.find("tools", args.tool)
            if tool is None:
                raise RegistryError(f"Unknown tool: {args.tool}")
            _print({"tool": tool, "runtime": detect_tools().get(args.tool, {"status": "UNKNOWN"})})
    except (AssetCatalogError, AssetReviewError, AtlasError, AudioCleanupError, BlenderWorkflowError, CapabilityResearchError, DeliveryError, EvidenceLibraryError, GameCreationError, GameplayReviewError, GenerationResearchError, GltfpackError, ImagePrepError, MeshValidationError, RegistryError, MediaError, SemanticVisionError, TextureProfileError, TextureValidationError, TimelineReviewError, TTSWorkflowError, TutorialReviewError, VisualEvidenceError, ValueError, WatchReviewError, FileNotFoundError, FileExistsError) as error:
        raise SystemExit(f"toolbox: {error}") from error
