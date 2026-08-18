from __future__ import annotations

import copy
import unittest

from toolbox.registry import Registry, RegistryError, load_registry, validate_registry


class RegistryTests(unittest.TestCase):
    def test_seed_registry_validates(self) -> None:
        registry = load_registry()
        self.assertEqual(registry.find("tools", "watch-skill")["adapter"], "adapters/watch.py")

    def test_duplicate_tool_id_is_rejected(self) -> None:
        registry = load_registry()
        data = copy.deepcopy(registry.data)
        data["tools"].append(copy.deepcopy(data["tools"][0]))
        with self.assertRaisesRegex(RegistryError, "duplicate id"):
            validate_registry(Registry(data))

    def test_unknown_capability_is_rejected(self) -> None:
        registry = load_registry()
        data = copy.deepcopy(registry.data)
        data["tools"][0]["capabilities"].append("not-a-real-capability")
        with self.assertRaisesRegex(RegistryError, "unknown capability"):
            validate_registry(Registry(data))

    def test_missing_adapter_is_rejected(self) -> None:
        registry = load_registry()
        data = copy.deepcopy(registry.data)
        data["tools"][0]["adapter"] = "adapters/missing.py"
        with self.assertRaisesRegex(RegistryError, "missing adapter"):
            validate_registry(Registry(data))

    def test_invalid_format_is_rejected(self) -> None:
        registry = load_registry()
        data = copy.deepcopy(registry.data)
        data["tools"][0]["formats"]["input"].append(".mp4")
        with self.assertRaisesRegex(RegistryError, "invalid format"):
            validate_registry(Registry(data))
