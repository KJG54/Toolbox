from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from toolbox.tts_workflow import TTSWorkflowError, synthesize


class _FakeEngine:
    def __init__(self) -> None:
        self.output: Path | None = None

    def setProperty(self, _name: str, _value: str) -> None:
        return None

    def save_to_file(self, _text: str, output: str) -> None:
        self.output = Path(output)

    def runAndWait(self) -> None:
        assert self.output is not None
        self.output.write_bytes(b"RIFFfixture")


class TextToSpeechWorkflowTests(unittest.TestCase):
    def test_synthesis_writes_a_derivative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "voice.wav"
            result = synthesize("hello", output, engine_factory=_FakeEngine)
            self.assertEqual(result["execution"], "local_only")
            self.assertGreater(output.stat().st_size, 0)

    def test_synthesis_rejects_non_wav_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(TTSWorkflowError, "wav"):
                synthesize("hello", Path(temporary) / "voice.mp3", engine_factory=_FakeEngine)
