"""Load and validate the versioned Toolbox capability catalog."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from .paths import REGISTRY_DIR, ROOT, SCHEMAS_DIR


class RegistryError(ValueError):
    """Raised when catalog metadata is malformed or internally inconsistent."""


@dataclass(frozen=True)
class Registry:
    data: dict[str, list[dict[str, Any]]]

    def records(self, kind: str) -> list[dict[str, Any]]:
        return list(self.data.get(kind, []))

    def find(self, kind: str, record_id: str) -> dict[str, Any] | None:
        return next((item for item in self.records(kind) if item["id"] == record_id), None)


REGISTRY_FILES = {
    "capabilities": "capabilities.yaml",
    "tools": "tools.yaml",
    "models": "models.yaml",
    "licenses": "licenses.yaml",
    "hardware_profiles": "hardware_profiles.yaml",
    "providers": "providers.yaml",
    "workflows": "workflows.yaml",
}

SCHEMA_FILES = {
    "capabilities": "capability.schema.json",
    "tools": "tool.schema.json",
    "models": "model.schema.json",
    "licenses": "license.schema.json",
    "hardware_profiles": "hardware_profile.schema.json",
    "providers": "provider.schema.json",
    "workflows": "workflow.schema.json",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        value = yaml.safe_load(source) or {}
    if not isinstance(value, dict):
        raise RegistryError(f"{path.relative_to(ROOT)} must contain a mapping at its root")
    return value


def load_registry(registry_dir: Path = REGISTRY_DIR) -> Registry:
    data: dict[str, list[dict[str, Any]]] = {}
    for kind, filename in REGISTRY_FILES.items():
        payload = _load_yaml(registry_dir / filename)
        records = payload.get(kind, [])
        if not isinstance(records, list):
            raise RegistryError(f"{filename}: {kind} must be a list")
        data[kind] = records
    registry = Registry(data=data)
    validate_registry(registry)
    return registry


def _schema_for(kind: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / SCHEMA_FILES[kind]
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_shape(kind: str, records: list[dict[str, Any]]) -> list[str]:
    schema = _schema_for(kind)
    if not schema:
        return []
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for position, record in enumerate(records):
        for error in validator.iter_errors(record):
            location = ".".join(str(part) for part in error.absolute_path)
            suffix = f".{location}" if location else ""
            errors.append(f"{kind}[{position}]{suffix}: {error.message}")
    return errors


def validate_registry(registry: Registry) -> None:
    errors: list[str] = []
    for kind, records in registry.data.items():
        errors.extend(_validate_shape(kind, records))
        ids = [record.get("id") for record in records]
        duplicates = sorted({record_id for record_id in ids if ids.count(record_id) > 1})
        errors.extend(f"{kind}: duplicate id '{record_id}'" for record_id in duplicates)

    capability_ids = {record["id"] for record in registry.records("capabilities")}
    license_ids = {record["id"] for record in registry.records("licenses")}
    tool_ids = {record["id"] for record in registry.records("tools")}
    for tool in registry.records("tools"):
        for capability in tool.get("capabilities", []):
            if capability not in capability_ids:
                errors.append(f"tool '{tool['id']}' references unknown capability '{capability}'")
        license_id = tool.get("license_id")
        if license_id not in license_ids:
            errors.append(f"tool '{tool['id']}' references unknown license '{license_id}'")
        adapter = tool.get("adapter")
        if adapter and not (ROOT / adapter).is_file():
            errors.append(f"tool '{tool['id']}' references missing adapter '{adapter}'")
        for fallback in tool.get("fallback_ids", []):
            if fallback not in tool_ids:
                errors.append(f"tool '{tool['id']}' references unknown fallback '{fallback}'")
        for format_name in tool.get("formats", {}).get("input", []) + tool.get("formats", {}).get("output", []):
            if not isinstance(format_name, str) or not format_name or format_name.startswith("."):
                errors.append(f"tool '{tool['id']}' has invalid format '{format_name}'")
    if errors:
        raise RegistryError("Registry validation failed:\n- " + "\n- ".join(errors))
