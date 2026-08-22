import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SUPABASE_URL", "https://example.invalid")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test")
os.environ.setdefault("MELI_APP_ID", "test")
os.environ.setdefault("MELI_APP_SECRET", "test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from questions_responder import _response_output_text


class OpenAIResponseParserTests(unittest.TestCase):
    def test_reads_raw_responses_api_output(self):
        payload = {
            "output": [{
                "type": "message",
                "content": [{"type": "output_text", "text": '{"risk":"LOW"}'}],
            }]
        }
        self.assertEqual(_response_output_text(payload), '{"risk":"LOW"}')

    def test_reads_sdk_style_output_text(self):
        self.assertEqual(
            _response_output_text({"output_text": '{"risk":"HIGH"}'}),
            '{"risk":"HIGH"}',
        )

    def test_missing_output_fails_closed(self):
        self.assertEqual(_response_output_text({"output": []}), "")


if __name__ == "__main__":
    unittest.main()
