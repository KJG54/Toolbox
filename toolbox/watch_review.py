"""Local-only orchestration for evidence-first Watch reviews."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .paths import ROOT


class WatchReviewError(ValueError):
    """Raised when a requested Watch review cannot safely run locally."""


def is_public_http_url(source: str) -> bool:
    """Return whether source is an HTTP(S) URL rather than a local media path."""
    parsed = urlparse(source.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def component_python() -> Path:
    """Return the preserved component's isolated interpreter."""
    executable = ROOT / "components" / "watch-skill" / ".venv" / "Scripts" / "python.exe"
    if not executable.is_file():
        raise WatchReviewError("Watch Skill is not installed; run toolbox doctor for the detected state")
    return executable


def build_timeline(result: Any, *, source_asset: str, pipeline: dict[str, Any]) -> dict[str, Any]:
    """Project a WatchResult into a stable, JSON-safe evidence timeline."""
    perception = result.perception
    frames = [] if perception is None else [
        {
            "kind": "frame",
            "timestamp_seconds": frame.timestamp_seconds,
            "path": str(frame.path),
            "scene_id": frame.scene_id,
            "selection_reason": frame.reason,
            "ocr_text": frame.ocr_text,
        }
        for frame in perception.frames
    ]
    transcript = [
        {
            "kind": "transcript",
            "start_seconds": segment.start,
            "end_seconds": segment.end,
            "text": segment.text,
            **({"speaker": segment.speaker} if segment.speaker else {}),
        }
        for segment in result.transcript.segments
    ]
    evidence = sorted(
        [*frames, *transcript],
        key=lambda item: item["timestamp_seconds"] if "timestamp_seconds" in item else item["start_seconds"],
    )
    metadata = result.metadata
    acquisition = result.acquisition
    return {
        "format": "toolbox-watch-review/v1",
        "created_at": datetime.now(UTC).isoformat(),
        "source_asset": source_asset,
        "pipeline": pipeline,
        "metadata": {
            "duration_seconds": metadata.duration_seconds,
            "width": metadata.width,
            "height": metadata.height,
            "fps": metadata.fps,
            "codec": metadata.codec,
            "has_audio": metadata.has_audio,
            "size_bytes": metadata.size_bytes,
        },
        "acquisition": {
            "source": acquisition.source,
            "kind": str(acquisition.kind),
            "acquirer": acquisition.acquirer,
            "from_cache": acquisition.from_cache,
            "video_path": str(acquisition.video_path) if acquisition.video_path else None,
        },
        "perception": {
            "engine": perception.engine if perception else None,
            "scene_count": perception.scene_count if perception else 0,
            "candidate_count": perception.candidate_count if perception else 0,
            "deduped_count": perception.deduped_count if perception else 0,
            "frames": frames,
        },
        "transcript": {"source": result.transcript.source, "segments": transcript},
        "evidence_timeline": evidence,
        "provenance": {
            "tool": "watch-skill",
            "component_version": "1.0.0",
            "license_status": "permitted",
            "execution": "local_only",
        },
    }


def run_watch_review(
    source: Path | str,
    output: Path,
    *,
    normalize: bool = False,
    max_width: int = 1280,
    max_frames: int | None = None,
    ocr: bool = False,
    local_whisper: bool = False,
    whisper_model: str | None = None,
    allow_download: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Run Watch in its component environment and persist a stable local timeline."""
    source_text = str(source).strip()
    is_url = is_public_http_url(source_text)
    if is_url and not allow_download:
        raise WatchReviewError(
            "A public video URL requires --allow-download; this is the explicit network permission for that one source"
        )
    if not is_url:
        source_path = Path(source_text).expanduser().resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"Media source does not exist: {source_path}")
        source_text = str(source_path)
    output = output.resolve()
    if output.suffix.casefold() != ".json":
        raise WatchReviewError("watch-review output must use a .json extension")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if not is_url and Path(source_text) == output:
        raise WatchReviewError("output must differ from source")

    work_dir = output.with_name(f"{output.stem}.watch-work")
    if work_dir.exists() and not overwrite:
        raise FileExistsError(f"Watch work directory already exists: {work_dir}; use --force or choose another output")
    work_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(component_python()),
        str(ROOT / "toolbox" / "watch_runner.py"),
        "--source", source_text,
        "--work-dir", str(work_dir),
    ]
    if is_url:
        command.append("--allow-download")
    if normalize:
        command.extend(["--normalize", "--max-width", str(max_width)])
    if max_frames is not None:
        command.extend(["--max-frames", str(max_frames)])
    if ocr:
        command.append("--ocr")
    if local_whisper:
        command.append("--local-whisper")
    if whisper_model:
        command.extend(["--whisper-model", whisper_model])

    environment = os.environ.copy()
    environment.update(
        {
            "WATCHSKILL_DATA_DIR": str(ROOT / "runtime" / "watch-skill"),
            "WATCHSKILL_CLOUD_STT_ENABLED": "false",
            "WATCHSKILL_OCR_ENABLED": "true" if ocr else "false",
            "WATCHSKILL_LOCAL_WHISPER_ENABLED": "true" if local_whisper else "false",
            # An explicit local-whisper request may use a cached model, but never downloads one.
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        }
    )
    completed = subprocess.run(command, text=True, capture_output=True, check=False, env=environment)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()[-1500:]
        raise WatchReviewError(f"Watch review failed: {detail}")
    try:
        timeline = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise WatchReviewError("Watch review returned malformed structured output") from error

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(timeline, indent=2) + "\n", encoding="utf-8")
    return {"output": str(output), "work_dir": str(work_dir), "timeline": timeline}
