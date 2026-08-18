"""Safe local FFmpeg normalization for reusable Toolbox media inputs."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class MediaError(ValueError):
    """Raised when a requested local media transformation is unsafe or invalid."""


def _binary(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise MediaError(f"{name} is not installed; run toolbox doctor for the detected state")
    return found


def probe_media(source: Path) -> dict[str, Any]:
    if not source.is_file():
        raise FileNotFoundError(f"Media source does not exist: {source}")
    result = subprocess.run(
        [_binary("ffprobe"), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(source)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise MediaError(f"ffprobe could not inspect {source.name}: {result.stderr.strip()[-500:]}")
    return json.loads(result.stdout)


def normalize_media(
    source: Path,
    output: Path,
    *,
    audio_only: bool = False,
    max_width: int = 1280,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create a portable MP4 proxy or mono 16 kHz WAV without touching the source."""
    source = source.resolve()
    output = output.resolve()
    if source == output:
        raise MediaError("output must differ from source; Toolbox never overwrites source media")
    if max_width < 64:
        raise MediaError("max_width must be at least 64 pixels")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")

    metadata = probe_media(source)
    streams = metadata.get("streams", [])
    has_video = any(stream.get("codec_type") == "video" for stream in streams)
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
    output.parent.mkdir(parents=True, exist_ok=True)

    if audio_only:
        if not has_audio:
            raise MediaError("source has no audio stream; cannot create an audio derivative")
        if output.suffix.casefold() != ".wav":
            raise MediaError("audio normalization output must use a .wav extension")
        command = [
            _binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y" if overwrite else "-n",
            "-i", str(source), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(output),
        ]
    else:
        if not has_video:
            raise MediaError("source has no video stream; use --audio-only for audio media")
        if output.suffix.casefold() != ".mp4":
            raise MediaError("video normalization output must use an .mp4 extension")
        command = [
            _binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y" if overwrite else "-n",
            "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?", "-map_metadata", "-1",
            "-vf", f"scale=w='min({max_width},iw)':h=-2:force_original_aspect_ratio=decrease",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000", "-movflags", "+faststart", str(output),
        ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode or not output.is_file() or output.stat().st_size == 0:
        raise MediaError(f"ffmpeg could not normalize {source.name}: {result.stderr.strip()[-1000:]}")
    return {
        "source": str(source),
        "output": str(output),
        "mode": "audio" if audio_only else "video_proxy",
        "source_metadata": metadata.get("format", {}),
        "output_metadata": probe_media(output).get("format", {}),
    }
