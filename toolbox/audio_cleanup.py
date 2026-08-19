"""Guarded local FFmpeg audio cleanup and edit derivatives."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .media import MediaError, _binary, probe_media


class AudioCleanupError(ValueError):
    """Raised when a requested audio cleanup cannot be performed safely."""


def clean_audio(
    source: Path,
    output: Path,
    *,
    normalize: bool = True,
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    source = source.resolve()
    output = output.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Audio source does not exist: {source}")
    if source == output:
        raise AudioCleanupError("Output must differ from source; Toolbox never overwrites audio sources")
    if output.suffix.casefold() not in {".wav", ".mp3", ".flac"}:
        raise AudioCleanupError("Audio cleanup output must use .wav, .mp3, or .flac")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if start_seconds is not None and start_seconds < 0:
        raise AudioCleanupError("start_seconds must be zero or greater")
    if end_seconds is not None and (end_seconds <= 0 or start_seconds is not None and end_seconds <= start_seconds):
        raise AudioCleanupError("end_seconds must be greater than start_seconds")
    metadata = probe_media(source)
    if not any(stream.get("codec_type") == "audio" for stream in metadata.get("streams", [])):
        raise AudioCleanupError("Source has no audio stream")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y" if overwrite else "-n"]
    if start_seconds is not None:
        command.extend(["-ss", str(start_seconds)])
    command.extend(["-i", str(source)])
    if end_seconds is not None:
        command.extend(["-to", str(end_seconds)])
    command.extend(["-map", "0:a:0", "-vn"])
    if normalize:
        command.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])
    if output.suffix.casefold() == ".wav":
        command.extend(["-c:a", "pcm_s16le"])
    elif output.suffix.casefold() == ".mp3":
        command.extend(["-c:a", "libmp3lame", "-q:a", "2"])
    else:
        command.extend(["-c:a", "flac"])
    command.append(str(output))
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode or not output.is_file() or output.stat().st_size == 0:
        raise AudioCleanupError(f"ffmpeg could not clean {source.name}: {completed.stderr.strip()[-1000:]}")
    return {
        "source": str(source),
        "output": str(output),
        "normalized": normalize,
        "trim": {"start_seconds": start_seconds, "end_seconds": end_seconds},
        "execution": "local_only",
    }
