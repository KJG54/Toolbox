from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from toolbox.paths import ROOT


class TextToSpeechExampleTests(unittest.TestCase):
    def test_offline_pyttsx3_example_writes_audio_in_temporary_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            working = Path(temporary)
            script = working / "tts.py"
            shutil.copy2(ROOT / "examples" / "tts" / "tts.py", script)
            result = subprocess.run([sys.executable, str(script)], cwd=working, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = working / "output.wav"
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)
