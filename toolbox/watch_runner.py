"""Component-interpreter bridge for the Toolbox Watch review workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# This file runs under Watch's component virtual environment.  Add Toolbox so
# it can use the stable serializer without coupling Watch's source to Toolbox.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from toolbox.watch_review import build_timeline
from watch_skill.watch import watch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--local-whisper", action="store_true")
    parser.add_argument("--whisper-model")
    args = parser.parse_args()
    result = watch(
        args.source,
        max_frames=args.max_frames,
        run_ocr=args.ocr,
        allow_local_whisper=args.local_whisper,
        allow_cloud_stt=False,
        whisper_model=args.whisper_model,
        out_dir=args.work_dir,
    )
    print(json.dumps(build_timeline(
        result,
        source_asset=args.source,
        pipeline={
            "workflow": "watch-review",
            "local_only": True,
            "cloud_stt": False,
            "ocr": args.ocr,
            "local_whisper": args.local_whisper,
            "whisper_model": args.whisper_model,
            "normalization": None,
        },
    )))


if __name__ == "__main__":
    main()
