import unittest
from unittest.mock import AsyncMock, patch

from app.models import ConversationSummary
from app.providers.openai_compatible import summarize_conversation


class ConversationSummaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_summary_uses_low_temperature_and_untrusted_history(self):
        history = [
            {"role": "user", "content": "من موسیقی سنتی دوست دارم."},
            {"role": "assistant", "content": "چه خوب."},
        ]
        with patch(
            "app.providers.openai_compatible._completion",
            new=AsyncMock(return_value="- علاقه به موسیقی سنتی"),
        ) as completion:
            result = await summarize_conversation(history)
        self.assertEqual(result, "- علاقه به موسیقی سنتی")
        args, kwargs = completion.call_args
        self.assertEqual(kwargs["temperature"], 0.1)
        self.assertEqual(args[0][0]["role"], "system")
        self.assertIn("Do not invent facts", args[0][0]["content"])
        self.assertEqual(args[0][1:], history)

    def test_summary_model_has_unique_session_constraint(self):
        table = ConversationSummary.__table__
        self.assertIn("session_id", table.c)
        self.assertTrue(table.c.session_id.unique)


if __name__ == "__main__":
    unittest.main()
