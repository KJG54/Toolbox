from __future__ import annotations

import subprocess
import sys
import unittest

from toolbox.paths import ROOT


class PreservationTests(unittest.TestCase):
    def test_baseline_manifest_verifies_import(self) -> None:
        result = subprocess.run([sys.executable, "scripts/verify_baseline_manifest.py"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
