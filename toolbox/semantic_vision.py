"""Pinned, local-only Florence-2 image understanding."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PIL import Image

from .paths import ROOT


class SemanticVisionError(ValueError):
    """Raised when the approved local semantic-vision runtime is unavailable."""


MODEL_ID = "microsoft/Florence-2-base"
MODEL_REVISION = "5ca5edf5bd017b9919c05d08aebef5e4c7ac3bac"
_TASKS = {
    "caption": "<CAPTION>",
    "detailed-caption": "<DETAILED_CAPTION>",
    "object-detection": "<OD>",
}


def _model_cache_path() -> Path:
    """Return the exact reviewed snapshot; never resolve a model through the network."""
    snapshot = Path.home() / ".cache" / "huggingface" / "hub" / "models--microsoft--Florence-2-base" / "snapshots" / MODEL_REVISION
    if not snapshot.is_dir():
        raise SemanticVisionError("Florence-2 is not cached locally; Toolbox will not download it during a request")
    return snapshot


def _load_runtime() -> tuple[Any, Any, Any, str]:
    modules_cache = ROOT / "cache" / "huggingface-modules"
    modules_cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_MODULES_CACHE", str(modules_cache))
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor
    except ImportError as error:
        raise SemanticVisionError("Local semantic vision dependencies are not installed; run toolbox doctor") from error
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device.startswith("cuda") else torch.float32
    snapshot = _model_cache_path()
    try:
        model = AutoModelForCausalLM.from_pretrained(
            snapshot,
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype=dtype,
        ).to(device)
        processor = AutoProcessor.from_pretrained(
            snapshot,
            trust_remote_code=True,
            local_files_only=True,
        )
    except OSError as error:
        raise SemanticVisionError("Florence-2 is not cached locally; Toolbox will not download it during a request") from error
    return torch, model, processor, device


def describe_image(source: Path, *, task: str = "caption") -> dict[str, Any]:
    """Run the explicitly approved local model against one image; never contacts a service."""
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Image source does not exist: {source}")
    if task not in _TASKS:
        raise SemanticVisionError(f"Unsupported semantic vision task: {task}")
    torch, model, processor, device = _load_runtime()
    prompt = _TASKS[task]
    with Image.open(source) as image:
        image = image.convert("RGB")
        inputs = processor(text=prompt, images=image, return_tensors="pt")
        inputs = {name: value.to(device, torch.float16 if device.startswith("cuda") else torch.float32) if value.is_floating_point() else value.to(device) for name, value in inputs.items()}
        with torch.no_grad():
            generated_ids = model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=256,
                num_beams=3,
            )
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        answer = processor.post_process_generation(generated_text, task=prompt, image_size=(image.width, image.height))
    return {
        "format": "toolbox-semantic-vision/v1",
        "source": str(source),
        "task": task,
        "answer": answer,
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "device": device,
        "execution": "local_only",
        "commercial_use": "allowed",
    }
