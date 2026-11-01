import unittest
from pydantic import ValidationError

from app.schemas import MemoryUpdate


class MemoryUpdateSchemaTests(unittest.TestCase):
    def test_partial_memory_update_accepts_only_importance(self):
        payload = MemoryUpdate(importance=5)
        self.assertEqual(payload.model_dump(exclude_unset=True), {"importance": 5})

    def test_memory_update_rejects_out_of_range_importance(self):
        with self.assertRaises(ValidationError):
            MemoryUpdate(importance=6)

    def test_memory_update_rejects_empty_content(self):
        with self.assertRaises(ValidationError):
            MemoryUpdate(content="")


if __name__ == "__main__":
    unittest.main()
