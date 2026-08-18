"""Local, source-preserving FFmpeg assembly of compatible video clips."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .media import MediaError, _binary, probe_media


def assemble_video(sources: list[Path], output: Path, *, overwrite: bool = False) -> dict[str, Any]:
    """Re-encode ordered local clips to a portable MP4 derivative."""
    if not sources:
        raise MediaError("At least one video source is required")
    resolved = [source.resolve() for source in sources]
    output = output.resolve()
    if output in resolved:
        raise MediaError("Output must differ from every source; Toolbox never overwrites source media")
    if output.suffix.casefold() != ".mp4":
        raise MediaError("Video assembly output must use .mp4")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    for source in resolved:
        data = probe_media(source)
        streams = data.get("streams", [])
        if not any(stream.get("codec_type") == "video" for stream in streams):
            raise MediaError(f"Source has no video stream: {source.name}")
        if not any(stream.get("codec_type") == "audio" for stream in streams):
            raise MediaError(f"Source has no audio stream: {source.name}; add audio before assembly")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y" if overwrite else "-n"]
    for source in resolved:
        command.extend(["-i", str(source)])
    labels = "".join(f"[{index}:v:0][{index}:a:0]" for index in range(len(resolved)))
    command.extend([
        "-filter_complex", f"{labels}concat=n={len(resolved)}:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-crf", "23", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-movflags", "+faststart", str(output),
    ])
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode or not output.is_file() or output.stat().st_size == 0:
        raise MediaError(f"ffmpeg could not assemble video: {completed.stderr.strip()[-1000:]}")
    return {"format": "toolbox-video-assembly/v1", "sources": [str(source) for source in resolved], "output": str(output), "execution": "local_only"}
