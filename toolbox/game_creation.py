"""Free, local-first game asset planning and procedural creation helpers."""

from __future__ import annotations

import hashlib
import json
import math
import random
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .timeline_review import load_timeline


class GameCreationError(ValueError):
    """Raised when a requested game-creation workflow is unsafe or invalid."""


_ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".wav", ".mp3", ".ogg", ".glb", ".gltf", ".fbx", ".obj", ".blend"}
_ENGINE_COMMANDS = {"godot": ["godot", "godot4"], "unity": ["Unity", "Unity.exe"], "unreal": ["UnrealEditor", "UnrealEditor.exe"]}


def _files(directory: Path, *, max_files: int = 10000) -> list[Path]:
    directory = directory.resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    found = [item for item in sorted(directory.rglob("*")) if item.is_file() and item.suffix.casefold() in _ASSET_EXTENSIONS and ".git" not in item.parts]
    if len(found) > max_files:
        raise GameCreationError(f"Directory exceeds the {max_files} asset safety limit")
    return found


def asset_naming_plan(directory: Path, *, max_files: int = 10000) -> dict[str, Any]:
    """Report a non-mutating game-asset naming normalization plan."""
    assets = _files(directory, max_files=max_files)
    proposals = []
    for asset in assets:
        stem = asset.stem.strip().lower().replace(" ", "_").replace("-", "_")
        normalized = "".join(char if char.isalnum() or char == "_" else "_" for char in stem)
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        normalized = normalized.strip("_") or "asset"
        target = f"{normalized}{asset.suffix.casefold()}"
        if asset.name != target:
            proposals.append({"source": str(asset.relative_to(directory.resolve())), "proposed_name": target, "reason": "lowercase_underscore_game_asset_name"})
    return {"format": "toolbox-game-asset-naming-plan/v1", "directory": str(directory.resolve()), "asset_count": len(assets), "rename_proposals": proposals, "mutation": "none", "execution": "local_only"}


def asset_manifest(directory: Path, *, max_files: int = 10000) -> dict[str, Any]:
    directory = directory.resolve()
    records = []
    for asset in _files(directory, max_files=max_files):
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        records.append({"path": str(asset.relative_to(directory)), "sha256": digest, "bytes": asset.stat().st_size})
    return {"format": "toolbox-game-asset-manifest/v1", "directory": str(directory), "assets": records, "execution": "local_only"}


def compare_asset_manifests(before: Path, after: Path) -> dict[str, Any]:
    def read(path: Path) -> dict[str, dict[str, Any]]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("format") != "toolbox-game-asset-manifest/v1":
            raise GameCreationError(f"Not a Toolbox game asset manifest: {path}")
        return {record["path"]: record for record in payload.get("assets", [])}
    left, right = read(before.resolve()), read(after.resolve())
    added = sorted(set(right) - set(left)); removed = sorted(set(left) - set(right))
    changed = sorted(path for path in set(left) & set(right) if left[path]["sha256"] != right[path]["sha256"])
    return {"format": "toolbox-game-asset-manifest-comparison/v1", "before": str(before.resolve()), "after": str(after.resolve()), "added": added, "removed": removed, "changed": changed, "unchanged": len(set(left) & set(right)) - len(changed), "execution": "local_only"}


def write_json(payload: dict[str, Any], output: Path, *, overwrite: bool = False) -> Path:
    output = output.resolve()
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output


def plan_watch_highlights(timeline_path: Path, *, max_clips: int = 8, minimum_gap_seconds: float = 5.0) -> dict[str, Any]:
    timeline = load_timeline(timeline_path)
    frames = timeline.get("perception", {}).get("frames", [])
    transcript = timeline.get("transcript", {}).get("segments", [])
    candidates = []
    last = -minimum_gap_seconds
    for frame in frames:
        timestamp = float(frame.get("timestamp_seconds", 0))
        if timestamp - last < minimum_gap_seconds:
            continue
        text = next((str(segment.get("text", "")).strip() for segment in transcript if float(segment.get("start_seconds", 0)) <= timestamp <= float(segment.get("end_seconds", 0)) and str(segment.get("text", "")).strip()), "")
        candidates.append({"start_seconds": max(0, round(timestamp - 2, 3)), "end_seconds": round(timestamp + 4, 3), "evidence_timestamp_seconds": timestamp, "evidence": text or "representative visual evidence frame"})
        last = timestamp
        if len(candidates) >= max_clips:
            break
    return {"format": "toolbox-watch-highlight-plan/v1", "timeline": str(timeline_path.resolve()), "clips": candidates, "selection": "representative_saved_evidence_only", "execution": "local_only"}


def video_contact_sheet(video: Path, output: Path, *, columns: int = 4, frames: int = 12, overwrite: bool = False) -> dict[str, Any]:
    video, output = video.resolve(), output.resolve()
    if not video.is_file():
        raise FileNotFoundError(f"Video does not exist: {video}")
    if output.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise GameCreationError("Contact sheet output must be an image")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if not 1 <= columns <= 12 or not 1 <= frames <= 48:
        raise GameCreationError("columns must be 1-12 and frames must be 1-48")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise GameCreationError("ffmpeg and ffprobe are required; run toolbox doctor")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video)], text=True, capture_output=True, check=False)
    duration = float(probe.stdout.strip() or 0)
    if duration <= 0:
        raise GameCreationError("Could not determine video duration")
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = math.ceil(frames / columns)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y" if overwrite else "-n", "-i", str(video), "-vf", f"fps={frames/duration:.8f},scale=320:-2,tile={columns}x{rows}:padding=4:margin=4", "-frames:v", "1", str(output)]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode or not output.is_file():
        raise GameCreationError(f"ffmpeg could not create contact sheet: {result.stderr.strip()[-800:]}")
    return {"format": "toolbox-video-contact-sheet/v1", "source": str(video), "output": str(output), "frames": frames, "columns": columns, "execution": "local_only"}


def generate_tone_asset(output: Path, *, kind: str, duration_seconds: float, seed: int = 1, overwrite: bool = False) -> dict[str, Any]:
    output = output.resolve()
    if output.suffix.casefold() != ".wav":
        raise GameCreationError("Procedural audio output must use .wav")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if kind not in {"coin", "jump", "hit", "laser", "ambient", "loop"}:
        raise GameCreationError("kind must be coin, jump, hit, laser, ambient, or loop")
    if not 0.08 <= duration_seconds <= 120:
        raise GameCreationError("duration must be between 0.08 and 120 seconds")
    rate, count, rng = 44100, int(44100 * duration_seconds), random.Random(seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    samples = bytearray()
    for index in range(count):
        time = index / rate; progress = index / max(1, count - 1)
        if kind == "coin": value = math.sin(2 * math.pi * (880 + 880 * progress) * time) * (1 - progress) ** 3
        elif kind == "jump": value = math.sin(2 * math.pi * (220 + 660 * progress) * time) * (1 - progress) ** 2
        elif kind == "hit": value = rng.uniform(-1, 1) * (1 - progress) ** 4
        elif kind == "laser": value = math.sin(2 * math.pi * (1400 - 1200 * progress) * time) * (1 - progress) ** 2
        elif kind == "ambient": value = (math.sin(2 * math.pi * 110 * time) + 0.5 * math.sin(2 * math.pi * 165 * time)) * 0.16
        else:
            beat = (time * 2) % 1
            value = (math.sin(2 * math.pi * (220 if int(time * 2) % 4 in {0, 2} else 330) * time) * 0.18) + (0.22 * math.sin(2 * math.pi * 80 * time) if beat < 0.08 else 0)
        sample = int(max(-1, min(1, value * 0.7)) * 32767)
        samples.extend(sample.to_bytes(2, "little", signed=True))
    with wave.open(str(output), "wb") as rendered:
        rendered.setnchannels(1); rendered.setsampwidth(2); rendered.setframerate(rate); rendered.writeframes(samples)
    return {"format": "toolbox-procedural-audio/v1", "kind": kind, "output": str(output), "duration_seconds": duration_seconds, "seed": seed, "generation": "deterministic_procedural_audio_not_ai", "execution": "local_only"}


def engine_readiness() -> dict[str, Any]:
    engines = {}
    for engine, commands in _ENGINE_COMMANDS.items():
        path = next((shutil.which(command) for command in commands if shutil.which(command)), None)
        engines[engine] = {"status": "READY" if path else "NOT_INSTALLED", "path": path, "cost": "free_tier_or_license_review_required"}
    return {"format": "toolbox-game-engine-readiness/v1", "engines": engines, "mutation": "none", "execution": "local_only"}


def scaffold_game_kit(output: Path, *, name: str, overwrite: bool = False) -> dict[str, Any]:
    output = output.resolve()
    if output.exists() and any(output.iterdir()) and not overwrite:
        raise FileExistsError(f"Game kit directory is not empty: {output}; use --force to add the standard folders")
    if not name.strip():
        raise GameCreationError("Game name must not be empty")
    folders = ["art/characters", "art/environment", "art/ui", "audio/music", "audio/sfx", "models", "materials", "scenes", "docs", "builds"]
    for folder in folders:
        (output / folder).mkdir(parents=True, exist_ok=True)
    manifest = {"format": "toolbox-game-kit/v1", "name": name.strip(), "folders": folders, "engine": "unselected", "asset_policy": "record source and license provenance before delivery", "created_by": "toolbox local scaffold"}
    manifest_path = output / "game-kit.json"
    if manifest_path.exists() and not overwrite:
        raise FileExistsError(f"Game kit manifest exists: {manifest_path}; use --force to replace it")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"format": "toolbox-game-kit/v1", "output": str(output), "manifest": str(manifest_path), "folders": folders, "execution": "local_only"}


def scaffold_godot_project(output: Path, *, name: str, overwrite: bool = False) -> dict[str, Any]:
    """Create an engine-neutral minimal Godot project definition without running Godot."""
    output = output.resolve()
    if output.exists() and any(output.iterdir()) and not overwrite:
        raise FileExistsError(f"Godot project directory is not empty: {output}; use --force to add the standard files")
    if not name.strip():
        raise GameCreationError("Godot project name must not be empty")
    for folder in ("assets/art", "assets/audio", "assets/models", "scenes", "scripts", "docs"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    project = output / "project.godot"
    project.write_text(
        "; Engine configuration file.\n; Generated by Toolbox; review in the Godot Project Settings UI.\n\n"
        "config_version=5\n\n[application]\n\n"
        f"config/name={json.dumps(name.strip())}\n"
        "run/main_scene=\"res://scenes/main.tscn\"\n\n[display]\n\n"
        "window/size/viewport_width=1280\nwindow/size/viewport_height=720\n"
        "window/size/window_width_override=1280\nwindow/size/window_height_override=720\n",
        encoding="utf-8",
    )
    scene = output / "scenes" / "main.tscn"
    scene.write_text("[gd_scene format=3]\n\n[node name=\"Main\" type=\"Node\"]\n", encoding="utf-8")
    gitignore = output / ".gitignore"
    if not gitignore.exists() or overwrite:
        gitignore.write_text(".godot/\n", encoding="utf-8")
    return {"format": "toolbox-godot-project/v1", "output": str(output), "project_file": str(project), "main_scene": str(scene), "godot_runtime": engine_readiness()["engines"]["godot"], "execution": "local_only", "note": "Scaffold only; open and validate the project in a locally installed Godot editor."}


def inspect_godot_project(project: Path) -> dict[str, Any]:
    root = project.resolve()
    project_file = root if root.name == "project.godot" else root / "project.godot"
    if not project_file.is_file():
        raise FileNotFoundError(f"Godot project.godot does not exist: {project_file}")
    content = project_file.read_text(encoding="utf-8", errors="replace")
    if "config_version=" not in content:
        raise GameCreationError("project.godot does not include config_version")
    assets = _files(project_file.parent)
    return {"format": "toolbox-godot-project-inspection/v1", "project": str(project_file.parent), "project_file": str(project_file), "asset_count": len(assets), "assets": [str(path.relative_to(project_file.parent).as_posix()) for path in assets], "godot_runtime": engine_readiness()["engines"]["godot"], "status": "READY_TO_OPEN" if engine_readiness()["engines"]["godot"]["status"] == "READY" else "PROJECT_VALID_RUNTIME_NOT_INSTALLED", "execution": "local_only"}


def map_godot_assets(project: Path) -> dict[str, Any]:
    """Report how local source assets would be placed under Godot res:// paths; never copy them."""
    project_root = project.resolve()
    if project_root.name == "project.godot":
        project_root = project_root.parent
    if not (project_root / "project.godot").is_file():
        raise FileNotFoundError(f"Godot project.godot does not exist: {project_root / 'project.godot'}")
    mapping = []
    for asset in _files(project_root):
        relative = asset.relative_to(project_root).as_posix()
        category = "texture" if asset.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"} else "audio" if asset.suffix.casefold() in {".wav", ".mp3", ".ogg"} else "model"
        mapping.append({"source": relative, "resource_path": f"res://{relative}", "category": category, "action": "Godot imports from the project folder when opened; Toolbox does not create import metadata"})
    return {"format": "toolbox-godot-import-map/v1", "project": str(project_root), "assets": mapping, "execution": "local_only", "mutation": "none"}


def plan_sprite_animations(layout: Path, *, separator: str = "_") -> dict[str, Any]:
    payload = json.loads(layout.resolve().read_text(encoding="utf-8"))
    if payload.get("format") != "toolbox-atlas-layout/v1" or not isinstance(payload.get("sprites"), list):
        raise GameCreationError("Sprite animation planning requires toolbox-atlas-layout/v1 metadata")
    if not separator:
        raise GameCreationError("separator must not be empty")
    groups: dict[str, list[dict[str, Any]]] = {}
    for position in payload["sprites"]:
        name = str(position.get("name", ""))
        stem = Path(name).stem
        animation = stem.split(separator, 1)[0] if separator in stem else stem
        groups.setdefault(animation, []).append({"name": name, "region": {key: position[key] for key in ("x", "y", "width", "height")}})
    animations = [{"name": name, "frames": frames, "suggested_fps": 8} for name, frames in sorted(groups.items())]
    return {"format": "toolbox-sprite-animation-plan/v1", "atlas": payload.get("atlas"), "layout": str(layout.resolve()), "separator": separator, "animations": animations, "execution": "local_only", "note": "Review grouping and create SpriteFrames/AnimatedSprite2D resources in the engine."}


def compare_gameplay_reviews(baseline: Path, candidate: Path) -> dict[str, Any]:
    def load(path: Path) -> dict[str, str]:
        payload = json.loads(path.resolve().read_text(encoding="utf-8"))
        if payload.get("format") != "toolbox-gameplay-review/v1":
            raise GameCreationError(f"Not a Toolbox gameplay review: {path}")
        return {str(item["id"]): str(item["status"]) for item in payload.get("findings", [])}
    before, after = load(baseline), load(candidate)
    changes = [{"id": item, "baseline": before.get(item, "NOT_PRESENT"), "candidate": after.get(item, "NOT_PRESENT")} for item in sorted(set(before) | set(after)) if before.get(item) != after.get(item)]
    regressions = [item for item in changes if item["baseline"] == "OBSERVED" and item["candidate"] != "OBSERVED"]
    return {"format": "toolbox-gameplay-regression/v1", "baseline": str(baseline.resolve()), "candidate": str(candidate.resolve()), "changes": changes, "regressions": regressions, "status": "REGRESSION_DETECTED" if regressions else "NO_OBSERVED_REGRESSIONS", "execution": "local_only"}


def audit_game_prototype(project: Path, *, require_build: bool = False) -> dict[str, Any]:
    root = project.resolve()
    if root.name == "project.godot":
        root = root.parent
    project_file = root / "project.godot"
    if not project_file.is_file():
        raise FileNotFoundError(f"Godot project.godot does not exist: {project_file}")
    assets = _files(root)
    asset_sidecars = [asset for asset in assets if asset.name != "project.godot"]
    missing_provenance = [asset.relative_to(root).as_posix() for asset in asset_sidecars if not asset.with_name(f"{asset.name}.provenance.json").is_file()]
    builds = [item for item in (root / "builds").rglob("*")] if (root / "builds").is_dir() else []
    build_files = [item for item in builds if item.is_file()]
    issues = []
    if missing_provenance:
        issues.append("asset_provenance_missing")
    if require_build and not build_files:
        issues.append("build_artifact_missing")
    return {"format": "toolbox-game-prototype-handoff/v1", "project": str(root), "asset_count": len(asset_sidecars), "missing_provenance": missing_provenance, "build_artifacts": [str(item.relative_to(root).as_posix()) for item in build_files], "issues": issues, "status": "READY_FOR_PROTOTYPE_HANDOFF" if not issues else "NEEDS_HANDOFF_REVIEW", "execution": "local_only", "limitations": "This checks project structure and recorded asset provenance; run the game and its engine-specific export checks separately."}
