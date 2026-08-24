"""Full public-source Watch orchestration with explicit network permission."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .paths import ROOT
from .watch_review import WatchReviewError, component_python, is_public_http_url


def run_full_watch(
    source: str,
    *,
    question: str = "What happens in this video?",
    allow_download: bool = False,
) -> dict[str, Any]:
    """Watch, index, and answer from one local file or owner-approved public URL."""
    source = source.strip()
    is_url = is_public_http_url(source)
    if is_url and not allow_download:
        raise WatchReviewError(
            "A public video URL requires --allow-download; this is the explicit network permission for that one source"
        )
    if not is_url:
        path = Path(source).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Media source does not exist: {path}")
        source = str(path)

    command = [
        str(component_python()),
        str(ROOT / "toolbox" / "full_watch_runner.py"),
        "--source",
        source,
        "--question",
        question,
    ]
    environment = os.environ.copy()
    environment.update(
        {
            "WATCHSKILL_DATA_DIR": str(ROOT / "runtime" / "watch-skill"),
            "WATCHSKILL_CLOUD_STT_ENABLED": "false",
            "WATCHSKILL_COST_POLICY": "offline_only",
            "WATCHSKILL_COBALT_API_URL": "",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        }
    )
    completed = subprocess.run(command, text=True, capture_output=True, check=False, env=environment)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()[-1500:]
        raise WatchReviewError(f"Full Watch failed: {detail}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise WatchReviewError("Full Watch returned malformed structured output") from error
    result["network_scope"] = "owner_approved_public_url" if is_url else "none"
    result["privacy"] = {
        "cloud_stt": "disabled",
        "cloud_vision": "disabled",
        "cookies_or_credentials": "not_used",
        "fallback_service": "disabled",
        "model_downloads": "disabled",
    }
    return result
