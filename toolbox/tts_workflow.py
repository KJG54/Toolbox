"""Guarded, local Windows speech synthesis with explicit readiness errors."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class TTSWorkflowError(ValueError):
    """Raised when local speech synthesis is unavailable or unsafe."""


def synthesize(text: str, output: Path, *, voice: str | None = None, overwrite: bool = False, engine_factory: Callable[[], Any] | None = None) -> dict[str, str]:
    """Write a local WAV derivative without changing the source text or existing output."""
    if not text.strip():
        raise TTSWorkflowError("Text to synthesize must not be empty")
    output = output.resolve()
    if output.suffix.casefold() != ".wav":
        raise TTSWorkflowError("Local Windows speech output must use a .wav extension")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        if engine_factory is None:
            import pyttsx3

            engine_factory = pyttsx3.init
        engine = engine_factory()
        if voice:
            engine.setProperty("voice", voice)
        engine.save_to_file(text, str(output))
        engine.runAndWait()
    except Exception as error:  # pyttsx3 exposes platform-specific COM failures.
        if "Access is denied" in str(error):
            raise TTSWorkflowError("Windows SAPI is unavailable to this process. Run from an interactive Windows session with a configured voice.") from error
        raise TTSWorkflowError(f"Local Windows speech synthesis failed: {error}") from error
    if not output.is_file() or output.stat().st_size == 0:
        raise TTSWorkflowError("Windows SAPI reported success but produced no audio file")
    return {"output": str(output), "tool": "windows-sapi-tts", "execution": "local_only"}
