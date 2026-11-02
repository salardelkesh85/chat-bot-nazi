import unittest
from unittest.mock import AsyncMock, patch

from app.providers.openai_compatible import (
    ProviderNotConfigured,
    _completion,
    is_local_provider,
    provider_is_configured,
)


class LocalProviderTests(unittest.IsolatedAsyncioTestCase):
    def test_loopback_provider_does_not_require_api_key(self):
        with patch("app.providers.openai_compatible.settings.ai_base_url", "http://127.0.0.1:11434/v1"), patch(
            "app.providers.openai_compatible.settings.ai_model", "qwen2.5:7b"
        ), patch("app.providers.openai_compatible.settings.ai_api_key", ""):
            self.assertTrue(is_local_provider())
            self.assertTrue(provider_is_configured())

    def test_remote_provider_requires_api_key(self):
        with patch("app.providers.openai_compatible.settings.ai_base_url", "https://api.example.com/v1"), patch(
            "app.providers.openai_compatible.settings.ai_model", "test-model"
        ), patch("app.providers.openai_compatible.settings.ai_api_key", ""):
            self.assertFalse(is_local_provider())
            self.assertFalse(provider_is_configured())

    async def test_local_completion_omits_authorization_header(self):
        response = AsyncMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"choices": [{"message": {"content": "سلام"}}]}
        client = AsyncMock()
        client.post.return_value = response
        with patch("app.providers.openai_compatible.settings.ai_base_url", "http://127.0.0.1:11434/v1"), patch(
            "app.providers.openai_compatible.settings.ai_model", "qwen2.5:7b"
        ), patch("app.providers.openai_compatible.settings.ai_api_key", ""), patch(
            "app.providers.openai_compatible.httpx.AsyncClient"
        ) as client_factory:
            client_factory.return_value.__aenter__.return_value = client
            result = await _completion([{"role": "user", "content": "سلام"}])
        self.assertEqual(result, "سلام")
        headers = client.post.call_args.kwargs["headers"]
        self.assertNotIn("Authorization", headers)

    async def test_remote_completion_without_key_fails_before_network(self):
        with patch("app.providers.openai_compatible.settings.ai_base_url", "https://api.example.com/v1"), patch(
            "app.providers.openai_compatible.settings.ai_model", "test-model"
        ), patch("app.providers.openai_compatible.settings.ai_api_key", ""):
            with self.assertRaises(ProviderNotConfigured):
                await _completion([{"role": "user", "content": "سلام"}])


if __name__ == "__main__":
    unittest.main()
