"""Review-only local generation research and hardware-fit assessment."""

from __future__ import annotations

from .paths import ROOT


class GenerationResearchError(ValueError):
    """Raised when an unsupported generation research topic is requested."""


_TOPICS = {
    "image": {
        "capability": "generate_image",
        "candidate": "FLUX.1 Schnell",
        "source": "https://huggingface.co/black-forest-labs/FLUX.1-schnell",
        "license_status": "apache-2.0_model_access_conditions_apply",
        "notes": "Owner-deferred: use an approved secondary image source instead. The official model card presents local Diffusers use, but access is gated and the listed transformer file is 23.8 GB. No runtime or weights are installed.",
    },
    "music": {
        "capability": "generate_music",
        "candidate": "ACE-Step 1.5",
        "source": "https://github.com/ACE-Step/ACE-Step-1.5",
        "license_status": "mit_verified",
        "notes": "Installed local component: pinned source, Python 3.12 runtime, and Ace-Step1.5 Turbo bundle. Current 6 GB profile disables the language model and uses INT8 plus CPU offload.",
    },
    "sfx": {
        "capability": "generate_sfx",
        "candidate": None,
        "source": None,
        "license_status": "deferred_by_owner",
        "notes": "Owner-deferred: use Toolbox procedural SFX. No AI sound-effect generator is selected or installed.",
    },
}


def research_generation(kind: str) -> dict[str, object]:
    kind = kind.casefold()
    if kind not in _TOPICS:
        raise GenerationResearchError("Generation research kind must be 'image', 'music', or 'sfx'")
    return {
        "format": "toolbox-generation-research/v1",
        "kind": kind,
        **_TOPICS[kind],
        "required_review": ([
            "Measure local VRAM and generation time before routing production work.",
            "Keep the 6 GB Turbo/no-LM profile unless stronger local hardware is available.",
        ] if kind == "music" else [
            "Verify the current project and model-weight licenses from official sources.",
            "Review downloaded code before execution.",
            "Measure local VRAM and generation time before routing production work.",
            "Obtain approval before installing the runtime or downloading model weights.",
        ]),
        "external_actions_performed": [],
        "mutations_performed": [],
    }


def evaluate_generation(kind: str) -> dict[str, object]:
    """Assess only the current local machine against reviewed candidate requirements."""
    import sys

    from .doctor import detect_hardware

    brief = research_generation(kind)
    hardware = detect_hardware()
    vram = max((gpu["vram_mb"] for gpu in hardware["gpus"]), default=0) / 1024
    if kind == "music":
        ace_root = ROOT / "components" / "ace-step"
        runtime = ace_root / ".venv" / "Scripts" / "python.exe"
        model = ace_root / "checkpoints" / "acestep-v15-turbo" / "model.safetensors"
        status = "LOCAL_SLOW" if runtime.is_file() and model.is_file() else "SETUP_REQUIRED"
        decision = "Installed ACE-Step Turbo is ready with the no-LM, INT8, CPU-offload profile. It is expected to be slow; measure each result before production use." if status == "LOCAL_SLOW" else "ACE-Step requires its isolated Python 3.11-3.12 runtime and local model bundle before use."
        requirements = {"documented_min_vram_gb": 4, "documented_recommended_vram_gb": 6, "documented_python": ["3.11", "3.12"]}
    elif kind == "image":
        status = "HARDWARE_UPGRADE_REQUIRED"
        decision = "The reviewed candidate has a 23.8 GB transformer file, is gated, and has no approved local runtime. Do not install on the current 6 GB GPU."
        requirements = {"listed_transformer_file_gb": 23.8, "model_access": "gated", "verified_vram_requirement": None}
    else:
        status = "NO_CANDIDATE"
        decision = "No sound-effect model has been selected, so no hardware or license decision can be made."
        requirements = {}
    return {
        "format": "toolbox-generation-evaluation/v1",
        "kind": kind,
        "candidate": brief["candidate"],
        "current_hardware": {"max_vram_gb": round(vram, 1), "gpus": hardware["gpus"], "python": f"{sys.version_info.major}.{sys.version_info.minor}"},
        "requirements": requirements,
        "license_status": brief["license_status"],
        "status": status,
        "decision": decision,
        "installation_performed": False,
        "external_actions_performed": [],
    }
