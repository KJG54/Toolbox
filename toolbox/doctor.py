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
    watch_packages = watch_root / ".venv" / "Lib" / "site-packages"
    perception_ready = all(
        (watch_packages / package).exists()
        for package in ("imagehash", "PIL", "cv2")
    )
    embeddings_ready = (watch_packages / "fastembed").exists()
    ocr_ready = all((watch_packages / package).exists() for package in ("rapidocr", "onnxruntime"))
    whisper_ready = (watch_packages / "faster_whisper").exists()
    whisper_tiny_cached = (Path.home() / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-tiny").is_dir()
    tts_root = ROOT / "examples" / "tts"
    ace_root = ROOT / "components" / "ace-step"
    ace_python = ace_root / ".venv" / "Scripts" / "python.exe"
    ace_turbo_model = ace_root / "checkpoints" / "acestep-v15-turbo" / "model.safetensors"
    gltfpack_binary = ROOT / "components" / "gltfpack" / "gltfpack.exe"
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
            "features": {
                "perception": "READY" if perception_ready else "NOT_INSTALLED",
                "semantic_index": "READY" if embeddings_ready else "KEYWORD_ONLY",
                "ocr": "READY" if ocr_ready else "NOT_INSTALLED",
                "local_whisper": "READY_TINY_MODEL" if whisper_ready and whisper_tiny_cached else "ENGINE_READY_CACHED_MODEL_REQUIRED" if whisper_ready else "NOT_INSTALLED",
                "cloud_stt": "EXTERNAL_OPT_IN",
            },
        },
        "tts-examples": {
            "status": "READY" if (tts_root / "tts.py").is_file() else "NOT_INSTALLED",
            "path": str(tts_root),
        },
        "ace-step-local": {
            "status": "READY_LOCAL_SLOW" if ace_python.is_file() and ace_turbo_model.is_file() else "SETUP_INCOMPLETE" if ace_root.is_dir() else "NOT_INSTALLED",
            "path": str(ace_root),
            "features": {
                "isolated_python": "READY" if ace_python.is_file() else "NOT_INSTALLED",
                "turbo_model": "READY" if ace_turbo_model.is_file() else "NOT_INSTALLED",
                "profile": "turbo_no_lm_int8_cpu_offload",
                "expected_performance": "LOCAL_SLOW",
            },
        },
        "ffmpeg": {
            "status": "READY" if shutil.which("ffmpeg") else "NOT_INSTALLED",
            "path": shutil.which("ffmpeg"),
        },
        "blender": {
            "status": "READY" if blender_binary else "NOT_INSTALLED",
            "path": blender_binary,
        },
        "gltfpack": {
            "status": "READY" if gltfpack_binary.is_file() else "NOT_INSTALLED",
            "path": str(gltfpack_binary) if gltfpack_binary.is_file() else None,
        },
    }


def doctor_report() -> dict[str, Any]:
    """Return detection results only; this function never downloads or repairs."""
    return {"hardware": detect_hardware(), "tools": detect_tools()}
