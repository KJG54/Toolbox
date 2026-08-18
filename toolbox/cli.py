"""Command-line interface for the local-first Toolbox."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .doctor import doctor_report, detect_hardware, detect_tools
from .provenance import create_sidecar, sidecar_path
from .registry import RegistryError, load_registry
from .routing import recommend


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
    except (RegistryError, FileNotFoundError, FileExistsError) as error:
        raise SystemExit(f"toolbox: {error}") from error
