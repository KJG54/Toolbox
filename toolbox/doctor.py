"""Read-only local hardware and installed-tool discovery."""

from __future__ import annotations

import platform
import shutil
import subprocess
import ctypes
from pathlib import Path
from typing import Any

from .paths import ROOT


def _run(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL, timeout=5).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def detect_hardware() -> dict[str, Any]:
    gpu_rows = _run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    gpus = []
    for row in (gpu_rows or "").splitlines():
        name, memory, driver = [part.strip() for part in row.split(",", maxsplit=2)]
        vram = int("".join(character for character in memory if character.isdigit()) or 0)
        gpus.append({"name": name, "vram_mb": vram, "driver": driver})
    return {
        "os": platform.platform(),
        "cpu": platform.processor() or "unknown",
        "ram_gb": _ram_gb(),
        "gpus": gpus,
    }


def _ram_gb() -> float | None:
    """Read physical memory through the Windows API without WMI permissions."""
    if platform.system() != "Windows":
        return None

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return round(status.ullTotalPhys / (1024**3), 1)


def detect_tools() -> dict[str, dict[str, Any]]:
    watch_root = ROOT / "components" / "watch-skill"
    tts_root = ROOT / "examples" / "tts"
    blender_roots = [
        Path.home() / "AppData" / "Local" / "Programs" / "Blender Foundation",
        Path("C:/Program Files/Blender Foundation"),
    ]
    blender_binary = shutil.which("blender")
    if not blender_binary:
        for root in blender_roots:
            if root.exists():
                match = next(root.rglob("blender.exe"), None)
                if match:
                    blender_binary = str(match)
                    break
    return {
        "watch-skill": {
            "status": "READY" if (watch_root / "pyproject.toml").is_file() else "NOT_INSTALLED",
            "path": str(watch_root),
        },
        "tts-examples": {
            "status": "READY" if (tts_root / "tts.py").is_file() else "NOT_INSTALLED",
            "path": str(tts_root),
        },
        "ffmpeg": {
            "status": "READY" if shutil.which("ffmpeg") else "NOT_INSTALLED",
            "path": shutil.which("ffmpeg"),
        },
        "blender": {
            "status": "READY" if blender_binary else "NOT_INSTALLED",
            "path": blender_binary,
        },
    }


def doctor_report() -> dict[str, Any]:
    """Return detection results only; this function never downloads or repairs."""
    return {"hardware": detect_hardware(), "tools": detect_tools()}
