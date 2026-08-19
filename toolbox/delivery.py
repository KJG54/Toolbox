"""Local handoff auditing and deterministic ZIP packaging."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from .provenance import sidecar_path


class DeliveryError(ValueError):
    """Raised when a handoff package would be incomplete or unsafe."""


_IGNORED = {".git", ".venv", "cache", "runtime", "__pycache__"}


def _root(directory: Path) -> Path:
    directory = directory.resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"Delivery directory does not exist: {directory}")
    return directory


def _files(root: Path, excluded: Path | None = None) -> list[Path]:
    return sorted(
        [
            path for path in root.rglob("*")
            if path.is_file() and path != excluded and not any(part.casefold() in _IGNORED for part in path.relative_to(root).parts)
        ],
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )


def audit_delivery(directory: Path, *, required: list[str] | None = None, require_provenance: bool = True) -> dict[str, Any]:
    """Validate local delivery contents without creating or altering any files."""
    root = _root(directory)
    required = required or []
    missing_required = [item for item in required if not (root / item).is_file()]
    artifacts = [path for path in _files(root) if not path.name.endswith(".provenance.json")]
    missing_provenance = [path.relative_to(root).as_posix() for path in artifacts if not sidecar_path(path).is_file()]
    malformed_provenance = []
    for artifact in artifacts:
        sidecar = sidecar_path(artifact)
        if sidecar.is_file():
            try:
                json.loads(sidecar.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                malformed_provenance.append(sidecar.relative_to(root).as_posix())
    issues = []
    if not artifacts:
        issues.append("no_delivery_artifacts")
    if missing_required:
        issues.append("required_files_missing")
    if require_provenance and missing_provenance:
        issues.append("provenance_missing")
    if malformed_provenance:
        issues.append("provenance_malformed")
    return {
        "format": "toolbox-delivery-audit/v1",
        "directory": str(root),
        "artifact_count": len(artifacts),
        "required": required,
        "missing_required": missing_required,
        "missing_provenance": missing_provenance if require_provenance else [],
        "malformed_provenance": malformed_provenance,
        "issues": issues,
        "status": "READY_FOR_HANDOFF" if not issues else "NEEDS_HANDOFF_REVIEW",
        "execution": "local_only",
    }


def package_delivery(
    directory: Path,
    output: Path,
    *,
    required: list[str] | None = None,
    require_provenance: bool = True,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create a ZIP only after the local delivery audit is ready."""
    root = _root(directory)
    output = output.resolve()
    if output.parent == root or root in output.parents:
        raise DeliveryError("Package output must be outside the delivery directory")
    if output.suffix.casefold() != ".zip":
        raise DeliveryError("Delivery package output must use .zip")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    audit = audit_delivery(root, required=required, require_provenance=require_provenance)
    if audit["status"] != "READY_FOR_HANDOFF":
        raise DeliveryError(f"Delivery audit did not pass: {', '.join(audit['issues'])}")
    output.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    with zipfile.ZipFile(output, mode, compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("toolbox-delivery-audit.json", json.dumps(audit, indent=2) + "\n")
        for path in _files(root):
            archive.write(path, path.relative_to(root).as_posix())
    return {
        "format": "toolbox-delivery-package/v1",
        "directory": str(root),
        "output": str(output),
        "artifact_count": audit["artifact_count"],
        "audit": audit,
        "execution": "local_only",
    }
