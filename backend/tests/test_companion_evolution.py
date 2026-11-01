import unittest
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from app.models import CompanionPreference
from app.providers.openai_compatible import extract_companion_insights
from app.schemas import PreferenceCreate


class CompanionEvolutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_extracts_only_allowed_preference_and_event_shapes(self):
        response = """{
          "preferences": [
            {"category": "communication_style", "content": "پاسخ کوتاه و صمیمی"},
            {"category": "private_secret", "content": "should be filtered"},
            {"category": "boundaries", "content": "قبل از ذخیره خاطره تأیید بگیر"}
          ],
          "events": [
            {"title": "اولین گفت‌وگوی طولانی", "description": "درباره داستان مشترک صحبت کردیم", "event_type": "first_time"},
            {"title": "invalid", "description": "", "event_type": "made_up"}
          ]
        }"""
        with patch(
            "app.providers.openai_compatible._completion",
            new=AsyncMock(return_value=response),
        ) as completion:
            result = await extract_companion_insights([{"role": "user", "content": "من پاسخ کوتاه دوست دارم."}])
        self.assertEqual(len(result["preferences"]), 2)
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(completion.call_args.kwargs["temperature"], 0.1)

    async def test_parses_fenced_json_response(self):
        response = chr(96) * 3 + 'json\\n{"preferences":[],"events":[]}\\n' + chr(96) * 3
        with patch(
            "app.providers.openai_compatible._completion",
            new=AsyncMock(return_value=response),
        ):
            self.assertEqual(await extract_companion_insights([{"role": "user", "content": "سلام"}]), {"preferences": [], "events": []})

    def test_preference_schema_rejects_unknown_categories(self):
        with self.assertRaises(ValidationError):
            PreferenceCreate(category="medical_profile", content="test")

    def test_preference_schema_accepts_user_confirmed_item(self):
        item = PreferenceCreate(category="format", content="پاسخ‌ها کوتاه باشند")
        self.assertEqual(item.category, "format")

    def test_preference_table_is_companion_scoped(self):
        table = CompanionPreference.__table__
        self.assertIn("companion_id", table.c)
        self.assertIn("content", table.c)


if __name__ == "__main__":
    unittest.main()
