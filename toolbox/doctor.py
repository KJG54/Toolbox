"""Read-only local hardware and installed-tool discovery."""

from __future__ import annotations

import platform
import shutil
import subprocess
import ctypes
import importlib.util
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
    visual_ready = all(importlib.util.find_spec(package) for package in ("cv2", "imagehash", "PIL"))
    semantic_runtime_ready = all(importlib.util.find_spec(package) for package in ("torch", "transformers", "huggingface_hub"))
    semantic_model_cached = (Path.home() / ".cache" / "huggingface" / "hub" / "models--microsoft--Florence-2-base" / "snapshots" / "5ca5edf5bd017b9919c05d08aebef5e4c7ac3bac").is_dir()
    semantic_device = _semantic_device() if semantic_runtime_ready else "NOT_INSTALLED"
    embeddings_ready = (watch_packages / "fastembed").exists()
    ocr_ready = all((watch_packages / package).exists() for package in ("rapidocr", "onnxruntime"))
    whisper_ready = (watch_packages / "faster_whisper").exists()
    whisper_tiny_cached = (Path.home() / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-tiny").is_dir()
    windows_voice_registry = _windows_voice_registry_present()
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
        "windows-sapi-tts": {
            "status": "READY_INTERACTIVE_SESSION_REQUIRED" if importlib.util.find_spec("pyttsx3") and windows_voice_registry else "VOICE_CONFIGURATION_REQUIRED" if importlib.util.find_spec("pyttsx3") else "NOT_INSTALLED",
            "path": "Windows Speech API (SAPI)",
            "features": {
                "voice_registry": "PRESENT" if windows_voice_registry else "NOT_CONFIGURED",
                "interactive_session_required": True,
            },
        },
        "local-visual-analysis": {
            "status": "READY" if visual_ready else "NOT_INSTALLED",
            "path": str(ROOT / "toolbox" / "visual_runner.py"),
            "features": {
                "pixel_comparison": "READY" if visual_ready else "NOT_INSTALLED",
                "semantic_model": "READY_LOCAL_MODEL" if semantic_runtime_ready and semantic_model_cached else "RUNTIME_READY_MODEL_NOT_CACHED" if semantic_runtime_ready else "NOT_INSTALLED",
                "semantic_device": semantic_device,
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
    }


def _windows_voice_registry_present() -> bool:
    if platform.system() != "Windows":
        return False


def _semantic_device() -> str:
    """Report the installed PyTorch acceleration mode without changing it."""
    try:
        import torch

        return "CUDA" if torch.cuda.is_available() else "CPU_ONLY_LOCAL_SLOW"
    except (ImportError, OSError):
        return "UNAVAILABLE"
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Speech\Voices\Tokens") as key:
            return winreg.QueryInfoKey(key)[0] > 0
    except OSError:
        return False


def doctor_report() -> dict[str, Any]:
    """Return detection results only; this function never downloads or repairs."""
    return {"hardware": detect_hardware(), "tools": detect_tools()}
