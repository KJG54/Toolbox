"""Thin adapter metadata for the preserved Watch component."""

from __future__ import annotations

from pathlib import Path

from toolbox.paths import ROOT


def component_root() -> Path:
    return ROOT / "components" / "watch-skill"


def command(*arguments: str) -> list[str]:
    """Return the component-local command without invoking it."""
    executable = component_root() / ".venv" / "Scripts" / "watch-skill.exe"
    return [str(executable), *arguments]
