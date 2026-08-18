from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from toolbox.media import MediaError, normalize_media


class MediaNormalizationTests(unittest.TestCase):
    def _fixture_video(self, directory: Path) -> Path:
        source = directory / "source.mp4"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=10",
                "-f", "lavfi", "-i", "sine=frequency=440", "-t", "1", "-pix_fmt", "yuv420p", str(source),
            ],
            check=True,
        )
        return source

    def test_normalize_video_creates_distinct_portable_derivative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._fixture_video(directory)
            output = directory / "proxy.mp4"
            result = normalize_media(source, output, max_width=160)
            self.assertEqual(result["mode"], "video_proxy")
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)
            self.assertTrue(source.is_file())

    def test_normalize_rejects_source_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = self._fixture_video(Path(temporary))
            with self.assertRaisesRegex(MediaError, "must differ"):
                normalize_media(source, source)

    def test_audio_mode_requires_wav_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = self._fixture_video(Path(temporary))
            with self.assertRaisesRegex(MediaError, r"\.wav"):
                normalize_media(source, source.with_name("audio.mp3"), audio_only=True)
