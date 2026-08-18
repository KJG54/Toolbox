"""Create a content manifest for the user-owned pre-Toolbox material."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "preservation" / "baseline-manifest.json"
EXCLUDED_PARTS = {".git", ".venv", ".pytest_cache", ".ruff_cache", "__pycache__"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return not any(part in EXCLUDED_PARTS for part in relative.parts)


def main() -> None:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not included(path):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("preservation/") or relative.startswith("scripts/"):
            continue
        files.append({"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size})

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "format": "toolbox-baseline-manifest/v1",
                "root": str(ROOT),
                "excluded_parts": sorted(EXCLUDED_PARTS),
                "files": files,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT} with {len(files)} files.")


if __name__ == "__main__":
    main()
