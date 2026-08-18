"""Local, source-preserving assembly of ordered audio clips."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .audio_cleanup import AudioCleanupError
from .media import _binary, probe_media


def assemble_audio(
    sources: list[Path],
    output: Path,
    *,
    normalize: bool = True,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Concatenate one or more local audio sources into a separate derivative."""
    if not sources:
        raise AudioCleanupError("At least one audio source is required")
    resolved = [source.resolve() for source in sources]
    output = output.resolve()
    if output in resolved:
        raise AudioCleanupError("Output must differ from every source; Toolbox never overwrites audio sources")
    if output.suffix.casefold() not in {".wav", ".mp3", ".flac"}:
        raise AudioCleanupError("Audio assembly output must use .wav, .mp3, or .flac")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    for source in resolved:
        if not source.is_file():
            raise FileNotFoundError(f"Audio source does not exist: {source}")
        metadata = probe_media(source)
        if not any(stream.get("codec_type") == "audio" for stream in metadata.get("streams", [])):
            raise AudioCleanupError(f"Source has no audio stream: {source.name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y" if overwrite else "-n"]
    for source in resolved:
        command.extend(["-i", str(source)])
    labels = "".join(f"[{index}:a:0]" for index in range(len(resolved)))
    filters = [f"{labels}concat=n={len(resolved)}:v=0:a=1[assembled]"]
    output_label = "[assembled]"
    if normalize:
        filters.append("[assembled]loudnorm=I=-16:TP=-1.5:LRA=11[normalized]")
        output_label = "[normalized]"
    command.extend(["-filter_complex", ";".join(filters), "-map", output_label])
    if output.suffix.casefold() == ".wav":
        command.extend(["-c:a", "pcm_s16le"])
    elif output.suffix.casefold() == ".mp3":
        command.extend(["-c:a", "libmp3lame", "-q:a", "2"])
    else:
        command.extend(["-c:a", "flac"])
    command.append(str(output))
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode or not output.is_file() or output.stat().st_size == 0:
        raise AudioCleanupError(f"ffmpeg could not assemble audio: {completed.stderr.strip()[-1000:]}")
    return {
        "format": "toolbox-audio-assembly/v1",
        "sources": [str(source) for source in resolved],
        "output": str(output),
        "normalized": normalize,
        "execution": "local_only",
    }
