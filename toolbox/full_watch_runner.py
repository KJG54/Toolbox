"""Bridge that restores Watch's URL resolver, index, and question engine."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from watch_skill.answer import answer_question
from watch_skill.index import index_watch_result
from watch_skill.watch import watch


def _acquisition(result) -> dict:
    acquisition = result.acquisition
    return {
        "source": acquisition.source,
        "kind": str(acquisition.kind),
        "acquirer": acquisition.acquirer,
        "from_cache": acquisition.from_cache,
        "title": acquisition.info.get("title"),
        "duration_seconds": acquisition.info.get("duration"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--question", required=True)
    args = parser.parse_args()

    work_root = Path.home() / "AppData" / "Local" / "Temp"
    work_dir = Path(tempfile.mkdtemp(prefix="toolbox-watch-", dir=work_root))
    result = watch(
        args.source,
        run_ocr=True,
        allow_local_whisper=True,
        allow_cloud_stt=False,
        whisper_model="tiny",
        out_dir=work_dir,
    )
    video_id = index_watch_result(result)
    answer = answer_question(video_id, args.question)
    print(json.dumps({
        "format": "toolbox-full-watch/v1",
        "video_id": video_id,
        "question": args.question,
        "answer": answer.to_dict(),
        "acquisition": _acquisition(result),
        "metadata": {
            "duration_seconds": result.metadata.duration_seconds,
            "width": result.metadata.width,
            "height": result.metadata.height,
            "has_audio": result.metadata.has_audio,
        },
        "work_dir": str(work_dir),
    }))


if __name__ == "__main__":
    main()
