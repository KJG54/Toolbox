"""Command-line interface for the local-first Toolbox."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .asset_review import AssetReviewError, assess_timeline, write_assessment
from .audio_cleanup import AudioCleanupError, clean_audio
from .asset_discovery import search_asset_sources
from .blender_workflow import BlenderWorkflowError, convert_3d, create_lod, inspect_blend, inspect_game_asset, preflight_blend, render_preview
from .capability_research import CapabilityResearchError, research_capability, write_research_brief
from .doctor import doctor_report, detect_hardware, detect_tools
from .evidence_library import EvidenceLibraryError, search_library
from .gameplay_review import GameplayReviewError, review_gameplay, write_gameplay_review
from .generation_research import GenerationResearchError, research_generation
from .image_prep import ImagePrepError, inspect_image_asset, prepare_image
from .media import MediaError, normalize_media
from .provenance import create_sidecar, sidecar_path
from .registry import RegistryError, load_registry
from .routing import recommend
from .semantic_vision import SemanticVisionError, describe_image
from .timeline_review import TimelineReviewError, answer_timeline, write_answer
from .tutorial_review import TutorialReviewError, verify_tutorial, write_tutorial_review
from .tts_workflow import TTSWorkflowError, synthesize
from .visual_evidence import VisualEvidenceError, compare_images, inspect_image
from .watch_review import WatchReviewError, run_watch_review


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
    blender_lod = blender_commands.add_parser("create-lod")
    blender_lod.add_argument("source", type=Path)
    blender_lod.add_argument("--output", type=Path, required=True)
    blender_lod.add_argument("--ratio", type=float, required=True)
    blender_lod.add_argument("--force", action="store_true")
    blender_lod.add_argument("--no-provenance", action="store_true")
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
    generation_research.add_argument("kind", choices=["music", "sfx"])
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
            else:
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
            elif args.blender_command == "create-lod":
                result = create_lod(args.source, args.output, ratio=args.ratio, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["blender"], source_assets=[str(args.source.resolve())],
                        human_modifications=f"Toolbox local decimate LOD derivative at ratio {args.ratio}", commercial_use="allowed", force=args.force,
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
            result = clean_audio(
                args.source, args.output, normalize=not args.no_normalize, start_seconds=args.start_seconds,
                end_seconds=args.end_seconds, overwrite=args.force,
            )
            if not args.no_provenance:
                result["provenance"] = str(create_sidecar(
                    args.output, tools=["ffmpeg"], source_assets=[str(args.source.resolve())],
                    human_modifications="Toolbox local audio cleanup", commercial_use="requires_review", force=args.force,
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
            else:
                result = research_generation(args.kind)
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
            else:
                _print({"sidecar": str(create_sidecar(args.asset, tools=args.tools, source_assets=args.source_assets, human_modifications=args.human_modifications, commercial_use=args.commercial_use, force=args.force))})
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
    except (AssetReviewError, AudioCleanupError, BlenderWorkflowError, CapabilityResearchError, EvidenceLibraryError, GameplayReviewError, GenerationResearchError, ImagePrepError, RegistryError, MediaError, SemanticVisionError, TimelineReviewError, TTSWorkflowError, TutorialReviewError, VisualEvidenceError, ValueError, WatchReviewError, FileNotFoundError, FileExistsError) as error:
        raise SystemExit(f"toolbox: {error}") from error
