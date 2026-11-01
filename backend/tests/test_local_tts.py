import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.local_tts import list_local_voices, voice_directory


class LocalTtsTests(unittest.TestCase):
    def test_lists_only_complete_local_piper_voice_pairs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "fa_voice.onnx").write_bytes(b"model")
            (root / "fa_voice.onnx.json").write_text("{}", encoding="utf-8")
            (root / "incomplete.onnx").write_bytes(b"model")
            with patch("app.services.local_tts.settings.voice_tts_model_dir", temp_dir):
                voices = list_local_voices()
            self.assertEqual([voice["id"] for voice in voices], ["fa_voice.onnx"])

    def test_voice_directory_resolves_configured_absolute_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("app.services.local_tts.settings.voice_tts_model_dir", temp_dir):
                self.assertEqual(voice_directory(), Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
