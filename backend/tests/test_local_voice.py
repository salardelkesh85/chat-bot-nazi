import unittest

from app.services.local_voice import (
    MAX_AUDIO_BYTES,
    normalize_audio_content_type,
    validate_audio_upload,
)


class LocalVoiceValidationTests(unittest.TestCase):
    def test_normalizes_audio_content_type_parameters(self):
        self.assertEqual(normalize_audio_content_type("audio/webm;codecs=opus"), "audio/webm")

    def test_accepts_supported_audio(self):
        validate_audio_upload("audio/webm;codecs=opus", 1024)

    def test_rejects_non_audio_content(self):
        with self.assertRaises(ValueError):
            validate_audio_upload("text/plain", 100)

    def test_rejects_empty_audio(self):
        with self.assertRaises(ValueError):
            validate_audio_upload("audio/wav", 0)

    def test_rejects_oversized_audio(self):
        with self.assertRaises(ValueError):
            validate_audio_upload("audio/wav", MAX_AUDIO_BYTES + 1)


if __name__ == "__main__":
    unittest.main()
