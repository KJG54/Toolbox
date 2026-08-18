"""Review-only research briefs for local music and sound-effect generation."""

from __future__ import annotations


class GenerationResearchError(ValueError):
    """Raised when an unsupported generation research topic is requested."""


_TOPICS = {
    "music": {
        "capability": "generate_music",
        "candidate": "ACE-Step",
        "source": "https://github.com/ace-step/ACE-Step",
        "license_status": "requires_review",
        "notes": "No model or runtime is installed. Verify the exact release, weights, dependencies, and hardware before installation.",
    },
    "sfx": {
        "capability": "generate_sfx",
        "candidate": None,
        "source": None,
        "license_status": "requires_research",
        "notes": "No local sound-effect generator has been selected or installed.",
    },
}


def research_generation(kind: str) -> dict[str, object]:
    kind = kind.casefold()
    if kind not in _TOPICS:
        raise GenerationResearchError("Generation research kind must be 'music' or 'sfx'")
    return {
        "format": "toolbox-generation-research/v1",
        "kind": kind,
        **_TOPICS[kind],
        "required_review": [
            "Verify the current project and model-weight licenses from official sources.",
            "Review downloaded code before execution.",
            "Measure local VRAM and generation time before routing production work.",
            "Obtain approval before installing the runtime or downloading model weights.",
        ],
        "external_actions_performed": [],
        "mutations_performed": [],
    }
