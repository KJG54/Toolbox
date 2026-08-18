"""The console-window audit — Windows must never flash a terminal at the user.

An agent spawns ``watch-skill`` with no console of its own. On Windows that
makes every console subprocess a potential focus-stealing window, so the rule is
absolute: nothing in src spawns a process without going through
``proc.hidden()`` / ``proc.background()``.

The subtle half is grandchildren, and it is what this file exists to pin down.
``CREATE_NO_WINDOW`` gives a child a real but window-less console that its own
children inherit — silence propagates. ``DETACHED_PROCESS`` gives it no console,
so each console grandchild allocates a fresh VISIBLE one; MSDN additionally
specifies CREATE_NO_WINDOW is *ignored* alongside DETACHED_PROCESS. That pairing
once made `ollama serve` open a terminal per model runner mid-pipeline. Hence:
DETACHED_PROCESS is banned outright, in source and in the shipped .cmd wrappers.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from watch_skill.proc import (
    DETACHED,
    HIDDEN_STARTUPINFO,
    NEW_GROUP,
    NO_WINDOW,
    background,
    hidden,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "watch_skill"
SPAWN_ATTRS = {"run", "Popen", "call", "check_call", "check_output"}
WRAPPERS = {"hidden", "background"}

win_only = pytest.mark.skipif(sys.platform != "win32", reason="Windows-only flags")


# --------------------------------------------------------------------------
# 1. The helpers themselves
# --------------------------------------------------------------------------

@win_only
def test_hidden_applies_no_window_and_hidden_startupinfo() -> None:
    kw = hidden()
    assert kw["creationflags"] & NO_WINDOW
    assert kw["startupinfo"] is HIDDEN_STARTUPINFO


@win_only
def test_hidden_strips_detached_process() -> None:
    """The exact pairing that opened a console on every grandchild."""
    kw = hidden(creationflags=subprocess.DETACHED_PROCESS | NEW_GROUP)
    assert not kw["creationflags"] & DETACHED, "DETACHED_PROCESS survived hidden()"
    assert kw["creationflags"] & NO_WINDOW
    assert kw["creationflags"] & NEW_GROUP, "unrelated caller flags must survive"


@win_only
def test_background_outlives_us_without_detaching() -> None:
    kw = background(stdout=subprocess.DEVNULL)
    assert kw["creationflags"] & NEW_GROUP, "Ctrl+C at us must not kill the helper"
    assert kw["creationflags"] & NO_WINDOW
    assert not kw["creationflags"] & DETACHED
    assert kw["stdout"] is subprocess.DEVNULL, "caller kwargs must pass through"


def test_helpers_are_noops_off_windows() -> None:
    if sys.platform == "win32":
        pytest.skip("Windows applies real flags")
    assert hidden() == {}
    assert "startupinfo" not in background()


# --------------------------------------------------------------------------
# 2. Every spawn in src is wrapped
# --------------------------------------------------------------------------

def _spawn_calls() -> list[tuple[Path, ast.Call]]:
    found = []
    for py in sorted(SRC.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if (isinstance(fn, ast.Attribute)
                    and isinstance(fn.value, ast.Name)
                    and fn.value.id == "subprocess"
                    and fn.attr in SPAWN_ATTRS):
                found.append((py, node))
    return found


def _is_wrapped(call: ast.Call) -> bool:
    """True when the call gets its flags from hidden()/background().

    Accepts ``**hidden()`` inline and ``**kwargs`` built by a wrapper earlier in
    the function — the latter is checked by the flag-level test below.
    """
    for kw in call.keywords:
        if kw.arg is not None:
            continue
        val = kw.value
        if isinstance(val, ast.Call) and isinstance(val.func, ast.Name) \
                and val.func.id in WRAPPERS:
            return True
        if isinstance(val, ast.Name):  # **kwargs assembled via a wrapper
            return True
    return False


def test_every_subprocess_spawn_is_console_suppressed() -> None:
    offenders = [
        f"{py.relative_to(ROOT)}:{node.lineno}"
        for py, node in _spawn_calls() if not _is_wrapped(node)
    ]
    assert not offenders, (
        "subprocess spawn without hidden()/background() — each one can flash a "
        "console window at the user:\n  " + "\n  ".join(offenders)
    )


def test_spawn_audit_actually_sees_the_call_sites() -> None:
    """Guard the guard: a refactor that renames the import must not mute it."""
    assert len(_spawn_calls()) >= 15


# --------------------------------------------------------------------------
# 3. DETACHED_PROCESS is banned everywhere it could reach a spawn
# --------------------------------------------------------------------------

def test_no_source_file_requests_detached_process() -> None:
    """Only proc.py may reference it — to strip it and to document why.

    AST-based, so comments and docstrings explaining the ban do not trip it;
    only a real ``subprocess.DETACHED_PROCESS`` load counts.
    """
    offenders = []
    for py in sorted(SRC.rglob("*.py")):
        if py.name == "proc.py":
            continue
        tree = ast.parse(py.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "DETACHED_PROCESS":
                offenders.append(f"{py.relative_to(ROOT)}:{node.lineno}")
            elif isinstance(node, ast.Name) and node.id == "DETACHED_PROCESS":
                offenders.append(f"{py.relative_to(ROOT)}:{node.lineno}")
    assert not offenders, (
        "DETACHED_PROCESS gives every console grandchild its own VISIBLE "
        "window; use proc.background() instead:\n  " + "\n  ".join(offenders)
    )


def test_shipped_cmd_wrappers_do_not_detach() -> None:
    offenders = [
        f"{cmd.relative_to(ROOT)}:{lineno}"
        for cmd in sorted(ROOT.glob("*.cmd"))
        for lineno, line in enumerate(
            cmd.read_text(encoding="utf-8-sig").splitlines(), 1)
        if "subprocess.DETACHED_PROCESS" in line
    ]
    assert not offenders, (
        "launcher wrapper detaches, so grandchildren get visible consoles:\n  "
        + "\n  ".join(offenders)
    )
