"""Command-line interface for the local-first Toolbox."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .asset_review import AssetReviewError, assess_timeline, write_assessment
from .blender_workflow import BlenderWorkflowError, convert_3d, inspect_blend
from .doctor import doctor_report, detect_hardware, detect_tools
from .evidence_library import EvidenceLibraryError, search_library
from .gameplay_review import GameplayReviewError, review_gameplay, write_gameplay_review
from .media import MediaError, normalize_media
from .provenance import create_sidecar, sidecar_path
from .registry import RegistryError, load_registry
from .routing import recommend
from .timeline_review import TimelineReviewError, answer_timeline, write_answer
from .tutorial_review import TutorialReviewError, verify_tutorial, write_tutorial_review
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
    blender_convert = blender_commands.add_parser("convert")
    blender_convert.add_argument("source", type=Path)
    blender_convert.add_argument("--output", type=Path, required=True)
    blender_convert.add_argument("--force", action="store_true")
    blender_convert.add_argument("--no-provenance", action="store_true")
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
            else:
                result = convert_3d(args.source, args.output, overwrite=args.force)
                if not args.no_provenance:
                    result["provenance"] = str(create_sidecar(
                        args.output, tools=["blender"], source_assets=[str(args.source.resolve())],
                        human_modifications="Toolbox local Blender conversion", commercial_use="allowed",
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
    except (AssetReviewError, BlenderWorkflowError, EvidenceLibraryError, GameplayReviewError, RegistryError, MediaError, TimelineReviewError, TutorialReviewError, WatchReviewError, FileNotFoundError, FileExistsError) as error:
        raise SystemExit(f"toolbox: {error}") from error
