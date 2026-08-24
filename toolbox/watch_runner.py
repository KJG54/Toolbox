"""Component-interpreter bridge for the Toolbox Watch review workflow."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

# This file runs under Watch's component virtual environment.  Add Toolbox so
# it can use the stable serializer without coupling Watch's source to Toolbox.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from toolbox.watch_review import build_timeline
from toolbox.media import normalize_media
from watch_skill.acquire.sources import classify_source, is_url_kind
from watch_skill.acquire.types import AcquireResult
from watch_skill.acquire.ytdlp import _download_once


def _download_public_source(source: str, work_dir: Path) -> AcquireResult:
    """Download one approved public URL without Watch's self-healing fallbacks.

    This deliberately calls only yt-dlp's single-attempt path: no self-update,
    Cobalt service, direct ffmpeg fallback, cookies, credentials, or installs.
    """
    kind = classify_source(source)
    if not is_url_kind(kind):
        raise ValueError("--allow-download is only valid for a public http(s) URL")
    downloaded = _download_once(source, work_dir / "download", audio_only=False)
    video_path = downloaded.get("video_path")
    if video_path is None:
        raise ValueError("The public URL did not provide downloadable media")
    return AcquireResult(
        source=source,
        kind=kind,
        video_path=Path(video_path),
        subtitle_path=downloaded.get("subtitle_path"),
        info=downloaded.get("info", {}),
        acquirer="yt-dlp-single-attempt",
    )


def _watch_preacquired(source: str, acquisition: AcquireResult, **kwargs):
    """Run Watch with a pre-acquired local file while retaining URL metadata."""
    watch_module = importlib.import_module("watch_skill.watch")
    original_acquire = watch_module.acquire
    watch_module.acquire = lambda *_args, **_kwargs: acquisition
    try:
        return watch_module.watch(source, **kwargs)
    finally:
        watch_module.acquire = original_acquire


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--max-width", type=int, default=1280)
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--local-whisper", action="store_true")
    parser.add_argument("--whisper-model")
    args = parser.parse_args()
    source_kind = classify_source(args.source)
    is_url = is_url_kind(source_kind)
    if is_url and not args.allow_download:
        raise ValueError("A public URL requires --allow-download")
    if not is_url and args.allow_download:
        raise ValueError("--allow-download is only valid for a public http(s) URL")

    acquisition = _download_public_source(args.source, args.work_dir) if is_url else None
    if acquisition is not None and args.normalize:
        proxy = args.work_dir / f"{acquisition.video_path.stem}.proxy.mp4"
        normalize_media(acquisition.video_path, proxy, max_width=args.max_width)
        acquisition.video_path = proxy

    watch_kwargs = {
        "max_frames": args.max_frames,
        "run_ocr": args.ocr,
        "allow_local_whisper": args.local_whisper,
        "allow_cloud_stt": False,
        "whisper_model": args.whisper_model,
        "out_dir": args.work_dir,
    }
    watch_module = importlib.import_module("watch_skill.watch")
    result = (
        _watch_preacquired(args.source, acquisition, **watch_kwargs)
        if acquisition
        else watch_module.watch(args.source, **watch_kwargs)
    )
    print(json.dumps(build_timeline(
        result,
        source_asset=args.source,
        pipeline={
            "workflow": "watch-review",
            "local_only": True,
            "public_url_download": is_url,
            "network_scope": "approved_public_url_only" if is_url else "none",
            "cloud_stt": False,
            "ocr": args.ocr,
            "local_whisper": args.local_whisper,
            "whisper_model": args.whisper_model,
            "normalization": {"created": True, "max_width": args.max_width} if args.normalize else None,
        },
    )))


if __name__ == "__main__":
    main()
