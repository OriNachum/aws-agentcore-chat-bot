import os
import sys
import unittest
from typing import cast
from unittest.mock import patch

# Ensure required environment variables are present before importing module under test.
os.environ.setdefault("DISCORD_BOT_TOKEN", "test-token")
os.environ.setdefault("DISCORD_CHANNEL_ID", "123456789")
os.environ.setdefault("BACKEND_MODE", "ollama")
os.environ.setdefault("OLLAMA_MODEL", "llama3")

class KnowledgeBaseUtilitiesTest(unittest.TestCase):
    def setUp(self) -> None:
        sys.modules.pop("community_bot.agentcore_app", None)

    def test_extract_content_from_dict_results_list(self) -> None:
        from importlib import import_module

        agentcore_app = import_module("community_bot.agentcore_app")
        _extract_content_from_result = agentcore_app._extract_content_from_result

        result = {
            "results": [
                {"content": "First chunk."},
                {"text": "Second chunk."},
                {"content": "   "},
            ]
        }

        extracted = _extract_content_from_result(result)

        self.assertIsNotNone(extracted)
        self.assertIsInstance(extracted, str)
        extracted_str = cast(str, extracted)
        self.assertIn("First chunk.", extracted_str)
        self.assertIn("Second chunk.", extracted_str)
        # Whitespace-only entries should be ignored.
        self.assertNotIn("   ", extracted_str)

    def test_extract_content_from_string(self) -> None:
        from importlib import import_module

        agentcore_app = import_module("community_bot.agentcore_app")
        _extract_content_from_result = agentcore_app._extract_content_from_result

        self.assertEqual(_extract_content_from_result("hello world"), "hello world")

    def test_kb_query_tool_empty_query_returns_error(self) -> None:
        from importlib import import_module

        agentcore_app = import_module("community_bot.agentcore_app")
        kb_query_tool = agentcore_app.kb_query_tool

        response = kb_query_tool("")

        self.assertEqual(response["status"], "error")
        self.assertIn("cannot be empty", response["content"][0]["text"].lower())

    @patch("community_bot.agentcore_app.query_knowledge_base_via_gateway")
    def test_kb_query_tool_success_includes_metadata_block(self, mock_query) -> None:
        from importlib import import_module

        agentcore_app = import_module("community_bot.agentcore_app")
        kb_query_tool = agentcore_app.kb_query_tool

        mock_query.return_value = {
            "content": "Example snippet about the topic.",
            "source": "direct",
            "raw": {"matches": 1},
        }

        response = kb_query_tool("Explain the topic", include_metadata=True)

        self.assertEqual(response["status"], "success")
        payload_text = response["content"][0]["text"]
        self.assertIn("Example snippet", payload_text)
        self.assertIn("Source: direct", payload_text)
        self.assertIn("```json", payload_text)
        # Ensure the metadata block is truncated below Discord limits.
        self.assertLessEqual(len(payload_text), 1900)


if __name__ == "__main__":
    unittest.main()


def tearDownModule() -> None:  # pragma: no cover
    sys.modules.pop("community_bot.agentcore_app", None)
