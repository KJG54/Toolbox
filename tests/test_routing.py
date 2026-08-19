from __future__ import annotations

import copy
import unittest

from toolbox.registry import Registry, load_registry
from toolbox.routing import HardwareOutcome, hardware_outcome, recommend


GPU_6 = {"gpus": [{"name": "RTX 2060", "vram_mb": 6144}]}
GPU_24 = {"gpus": [{"name": "RTX 3090", "vram_mb": 24576}]}
CPU_ONLY = {"gpus": []}


class RoutingTests(unittest.TestCase):
    def test_blender_is_local_slow_on_current_profile(self) -> None:
        registry = load_registry()
        blender = registry.find("tools", "blender")
        self.assertEqual(hardware_outcome(blender, GPU_6), HardwareOutcome.LOCAL_SLOW)
        self.assertEqual(hardware_outcome(blender, GPU_24), HardwareOutcome.LOCAL_OK)

    def test_gpu_required_tool_requires_upgrade_on_cpu_only(self) -> None:
        registry = load_registry()
        tool = copy.deepcopy(registry.find("tools", "blender"))
        tool["hardware"] = {"gpu_required": True, "min_vram_gb": 8}
        self.assertEqual(hardware_outcome(tool, CPU_ONLY), HardwareOutcome.HARDWARE_UPGRADE_REQUIRED)

    def test_commercial_gate_rejects_unreviewed_tts(self) -> None:
        result = recommend("text_to_speech", commercial=True, registry=load_registry(), hardware=GPU_6, installed={})
        self.assertTrue(result["capability_gap"])
        self.assertIn("commercial-use status is not approved", result["rejected"][0]["reasons"])

    def test_external_tool_needs_explicit_approval(self) -> None:
        registry = load_registry()
        data = copy.deepcopy(registry.data)
        external = copy.deepcopy(data["tools"][0])
        external.update({"id": "external-watch", "external_opt_in": True, "routing_priority": 200})
        data["tools"].append(external)
        result = recommend("watch_video", registry=Registry(data), hardware=GPU_6, installed={})
        external_rejection = next(item for item in result["rejected"] if item["id"] == "external-watch")
        self.assertIn("external service requires explicit approval", external_rejection["reasons"])

    def test_unknown_capability_returns_research_brief(self) -> None:
        result = recommend("generate_video", registry=load_registry(), hardware=GPU_6, installed={})
        self.assertTrue(result["capability_gap"])
        self.assertIn("Research candidates", result["next_action"])

    def test_ace_step_is_routable_but_local_slow_on_current_gpu(self) -> None:
        result = recommend(
            "generate_music",
            registry=load_registry(),
            hardware=GPU_6,
            installed={"ace-step-local": {"status": "READY_LOCAL_SLOW"}},
        )
        self.assertEqual(result["recommendations"][0]["id"], "ace-step-local")
        self.assertTrue(result["recommendations"][0]["installed"])
        self.assertEqual(result["recommendations"][0]["hardware"], HardwareOutcome.LOCAL_SLOW)
