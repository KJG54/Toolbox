"""Component-interpreter bridge for local visual feature analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import imagehash
import numpy
from PIL import Image


def _load(path: Path) -> numpy.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"OpenCV could not decode {path}")
    return image


def _signature(path: Path) -> dict[str, object]:
    image = _load(path)
    height, width = image.shape[:2]
    mean_bgr = [round(float(value), 2) for value in image.mean(axis=(0, 1))]
    return {
        "source": str(path),
        "width": width,
        "height": height,
        "aspect_ratio": round(width / height, 5),
        "mean_bgr": mean_bgr,
        "perceptual_hash": str(imagehash.phash(Image.open(path).convert("RGB"))),
        "analysis_level": "pixel_and_perceptual_features",
        "semantic_model": "NOT_INSTALLED",
        "execution": "local_only",
    }


def inspect(path: Path) -> dict[str, object]:
    return {"format": "toolbox-visual-evidence/v1", "mode": "inspect", **_signature(path)}


def compare(reference: Path, candidate: Path) -> dict[str, object]:
    reference_image = _load(reference)
    candidate_image = _load(candidate)
    candidate_height, candidate_width = candidate_image.shape[:2]
    reference_resized = cv2.resize(reference_image, (candidate_width, candidate_height), interpolation=cv2.INTER_AREA)
    difference = cv2.absdiff(reference_resized, candidate_image)
    mean_absolute_difference = round(float(difference.mean()), 3)
    changed_ratio = round(float((difference.max(axis=2) > 24).mean()), 5)
    status = "VISUALLY_SIMILAR" if mean_absolute_difference <= 5 and changed_ratio <= 0.02 else "VISUAL_DIFFERENCE_DETECTED"
    return {
        "format": "toolbox-visual-evidence/v1",
        "mode": "compare",
        "reference": _signature(reference),
        "candidate": _signature(candidate),
        "mean_absolute_difference": mean_absolute_difference,
        "changed_pixel_ratio": changed_ratio,
        "status": status,
        "execution": "local_only",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_command = commands.add_parser("inspect")
    inspect_command.add_argument("source", type=Path)
    compare_command = commands.add_parser("compare")
    compare_command.add_argument("reference", type=Path)
    compare_command.add_argument("candidate", type=Path)
    args = parser.parse_args()
    result = inspect(args.source) if args.command == "inspect" else compare(args.reference, args.candidate)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
