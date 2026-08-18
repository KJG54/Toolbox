"""Verify that every preserved pre-Toolbox file survived its planned migration."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "preservation" / "baseline-manifest.json"
TRANSFORMATIONS = ROOT / "preservation" / "intentional-transformations.json"


def destination(old: str) -> Path:
    replacements = (
        ("Watch Skill/watch-skill/", "components/watch-skill/"),
        ("Watch Skill/README.md", "docs/watch-local-install.md"),
        ("Text to Speech/", "examples/tts/"),
        ("Text to Speech Artifacts/", "outputs/tts/"),
        ("Watch Skill Artifacts/", "outputs/watch/"),
        ("IDEA.md", "docs/idea.md"),
    )
    for prefix, target in replacements:
        if old.startswith(prefix):
            return ROOT / (target + old[len(prefix) :])
    return ROOT / old


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    transformations = json.loads(TRANSFORMATIONS.read_text(encoding="utf-8"))
    allowed = {entry["original"] for entry in transformations["transformations"]}
    failures = []
    for record in payload["files"]:
        path = destination(record["path"])
        if not path.is_file():
            failures.append(f"missing: {record['path']} -> {path.relative_to(ROOT)}")
        elif digest(path) != record["sha256"] and record["path"] not in allowed:
            failures.append(f"changed: {record['path']} -> {path.relative_to(ROOT)}")
    if failures:
        print("Baseline verification failed:\n" + "\n".join(failures))
        return 1
    print(f"Baseline verified: {len(payload['files'])} files preserved; {len(allowed)} documented transformations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
