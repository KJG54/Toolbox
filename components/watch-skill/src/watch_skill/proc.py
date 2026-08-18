"""LOCAL MODULE: Windows console-window suppression for spawned subprocesses.

On Windows, a Python process with no attached console — exactly how an AI agent
spawns ``watch-skill`` — gets a brand-new console window for every console
subprocess it starts. Each window appears for milliseconds and disappears, and
because Windows grants foreground activation to a newly created window, each one
steals focus from whatever the user is typing into. ``doctor`` is the worst case:
it shells out to nvidia-smi, ffmpeg, yt-dlp (twice), deno, and ollama in quick
succession, producing a burst of focus-stealing flashes.

Two flags are needed to fully suppress this:

* ``CREATE_NO_WINDOW`` — stops the child from *allocating a new console*.
* A hidden ``STARTUPINFO`` (wShowWindow=SW_HIDE) — stops a console-subsystem
  child (ffmpeg.exe, yt-dlp.exe, deno.exe) from flashing a visible window for the
  brief moment it runs.

``CREATE_NO_WINDOW`` alone still leaves a transient focus-stealing flash on some
console binaries; pairing it with the hidden STARTUPINFO removes it entirely.
Neither flag detaches an inherited console, so a subprocess run from a real
terminal still streams its output normally — and both are no-ops off Windows
(STARTUPINFO is Windows-only and NO_WINDOW is 0 there).

Usage — spread into any subprocess call::

    subprocess.run(cmd, capture_output=True, **hidden())

Grandchildren are the whole point
---------------------------------
``CREATE_NO_WINDOW`` does not merely hide a window — it gives the child a real
but *window-less* console object, which the child's own children then inherit.
That is what keeps ffmpeg-spawned-by-yt-dlp silent even though we never touch
that inner spawn.

``DETACHED_PROCESS`` looks similar and is a trap. It gives the child *no console
at all*, so the moment that child spawns a console program, Windows allocates a
brand-new console for the grandchild — **with a visible window**. MSDN also
specifies that ``CREATE_NO_WINDOW`` is *ignored* when combined with
``DETACHED_PROCESS``, so the pairing that reads like "detached and quiet" is in
fact "detached and loud". Measured behaviour, from a console-less parent:

===============================  ==============  ====================
flags                            child console   grandchild console
===============================  ==============  ====================
(none)                           visible         visible (inherited)
CREATE_NO_WINDOW                 none            none (inherited)
DETACHED_PROCESS | NO_WINDOW     none            **visible, new**
===============================  ==============  ====================

This bit us via ``ollama serve``: started with DETACHED_PROCESS, it stayed
invisible itself while every model runner it forked opened its own console
window — a burst of focus-stealing terminals mid-pipeline. So ``hidden()``
*strips* DETACHED_PROCESS rather than composing with it, and long-lived helpers
should use ``background()`` below, which outlives us without it.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any

__all__ = ["NO_WINDOW", "NEW_GROUP", "DETACHED", "hidden", "background",
           "HIDDEN_STARTUPINFO"]

#: ``subprocess.CREATE_NO_WINDOW`` on Windows, else 0 (falsy — nothing applied).
NO_WINDOW: int = (
    getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
)

#: ``CREATE_NEW_PROCESS_GROUP`` — shields a background child from the Ctrl+C
#: that reaches our own process group. Safe: it does not affect consoles.
NEW_GROUP: int = (
    getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if sys.platform == "win32" else 0
)

#: ``DETACHED_PROCESS`` — never set this. Named only so ``hidden()`` can strip it
#: and tests can assert it is absent. See the module docstring for why.
DETACHED: int = (
    getattr(subprocess, "DETACHED_PROCESS", 0) if sys.platform == "win32" else 0
)

#: A hidden-window STARTUPINFO, created only on Windows. Spreading this into a
#: subprocess call makes the child's console window hidden rather than flashed.
HIDDEN_STARTUPINFO: "subprocess.STARTUPINFO | None" = None
if sys.platform == "win32":
    _si = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
    _si.dwFlags = subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
    _si.wShowWindow = subprocess.SW_HIDE  # type: ignore[attr-defined]
    HIDDEN_STARTUPINFO = _si


def hidden(**kwargs: Any) -> dict[str, Any]:
    """Return ``kwargs`` with console suppression applied for the child.

    On Windows this OR-s ``CREATE_NO_WINDOW`` into ``creationflags``, injects a
    hidden ``STARTUPINFO``, and **clears ``DETACHED_PROCESS``** — that flag would
    push a visible console onto every grandchild and silently void
    CREATE_NO_WINDOW (see module docstring). Other caller flags, notably
    ``CREATE_NEW_PROCESS_GROUP``, are preserved. No-op off Windows.
    """
    if not NO_WINDOW:
        return kwargs
    flags = kwargs.get("creationflags", 0)
    kwargs["creationflags"] = (flags & ~DETACHED) | NO_WINDOW
    if "startupinfo" not in kwargs and HIDDEN_STARTUPINFO is not None:
        kwargs["startupinfo"] = HIDDEN_STARTUPINFO
    return kwargs


def background(**kwargs: Any) -> dict[str, Any]:
    """Flags for a helper that must outlive us and never show a window.

    Windows keeps a child alive after its parent exits by default, so surviving
    us costs no flag at all — ``DETACHED_PROCESS`` buys nothing here and costs a
    console window on every grandchild. What we do want is
    ``CREATE_NEW_PROCESS_GROUP`` (a Ctrl+C aimed at us must not kill the helper)
    plus the usual ``hidden()`` suppression, which the helper's own children then
    inherit. Callers should still route stdio to DEVNULL. No-op off Windows,
    where POSIX callers want ``start_new_session=True`` instead.
    """
    if not NO_WINDOW:
        return kwargs
    return hidden(creationflags=kwargs.pop("creationflags", 0) | NEW_GROUP, **kwargs)
