"""Command-line interface for the local-first Toolbox."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .doctor import doctor_report, detect_hardware, detect_tools
from .media import MediaError, normalize_media
from .provenance import create_sidecar, sidecar_path
from .registry import RegistryError, load_registry
from .routing import recommend
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
    except (RegistryError, MediaError, WatchReviewError, FileNotFoundError, FileExistsError) as error:
        raise SystemExit(f"toolbox: {error}") from error
