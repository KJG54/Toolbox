"""Stable paths relative to the Toolbox checkout."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "registry"
SCHEMAS_DIR = ROOT / "schemas"
COMPONENTS_DIR = ROOT / "components"
