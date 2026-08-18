from __future__ import annotations

import unittest

from adapters.watch import command, component_root


class WatchAdapterTests(unittest.TestCase):
    def test_adapter_points_to_preserved_component(self) -> None:
        self.assertTrue((component_root() / "src" / "watch_skill" / "watch.py").is_file())
        self.assertTrue(command("doctor")[0].endswith("watch-skill.exe"))
