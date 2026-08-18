"""Agent Creator Toolbox public package."""

from typing import Any

__all__ = ["HardwareOutcome", "recommend"]


def __getattr__(name: str) -> Any:
    """Keep lightweight adapters usable from a component-only environment."""
    if name in __all__:
        from .routing import HardwareOutcome, recommend

        return {"HardwareOutcome": HardwareOutcome, "recommend": recommend}[name]
    raise AttributeError(name)
