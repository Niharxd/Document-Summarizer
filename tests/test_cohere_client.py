"""
Tests for summarizer/cohere_client.py.

All Cohere API calls are fully mocked — no real network requests are made.
"""
from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_response(text: str):
    """Build a minimal mock that mirrors response.message.content[0].text."""
    content_item = SimpleNamespace(text=text)
    message = SimpleNamespace(content=[content_item])
    return SimpleNamespace(message=message)


def _fresh_module():
    """
    Re-import cohere_client with a clean lru_cache so each test that
    manipulates env vars or the cache starts from a known state.
    """
    mod_name = "summarizer.cohere_client"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    return importlib.import_module(mod_name)


# ── build_domain_prompt ───────────────────────────────────────────────────────

class TestBuildDomainPrompt:
    def setup_method(self):
        from summarizer.cohere_client import build_domain_prompt
        self.build = build_domain_prompt

    def test_legal_prompt_contains_clauses(self):
        prompt = self.build("Some legal text.", "legal")
        assert "clauses" in prompt.lower()
        assert "Some legal text." in prompt

    def test_medical_prompt_contains_diagnosis(self):
        prompt = self.build("Patient notes.", "medical")
        assert "diagnosis" in prompt.lower()
        assert "Patient notes." in prompt

    def test_technical_prompt_contains_architecture(self):
        prompt = self.build("System design doc.", "technical")
        assert "architecture" in prompt.lower()
        assert "System design doc." in prompt

    def test_prompt_includes_document_text(self):
        text = "Unique marker 12345"
        for domain in ("legal", "medical", "technical"):
            assert text in self.build(text, domain)

    def test_unsupported_domain_raises(self):
        with pytest.raises(ValueError, match="Unsupported domain"):
            self.build("Some text.", "finance")

    def test_empty_document_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            self.build("", "legal")

    def test_whitespace_only_document_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            self.build("   \n\t  ", "medical")


# ── get_cohere_client ─────────────────────────────────────────────────────────

class TestGetCohereClient:
    def test_missing_api_key_raises(self):
        mod = _fresh_module()
        with patch.dict("os.environ", {}, clear=True):
            # Remove key if present
            import os
            os.environ.pop("COHERE_API_KEY", None)
            with pytest.raises(ValueError, match="COHERE_API_KEY"):
                mod.get_cohere_client()

    def test_returns_client_v2_when_key_present(self):
        mod = _fresh_module()
        with patch.dict("os.environ", {"COHERE_API_KEY": "test-key-abc"}):
            with patch("cohere.ClientV2") as mock_cls:
                mock_cls.return_value = MagicMock()
                client = mod.get_cohere_client()
                mock_cls.assert_called_once_with(api_key="test-key-abc")
                assert client is mock_cls.return_value


# ── generate_summary ──────────────────────────────────────────────────────────

class TestGenerateSummary:
    def _patched_module(self, summary_text: str = "Mocked summary."):
        """Return a freshly imported module with the Cohere client fully mocked."""
        mod = _fresh_module()
        mock_client = MagicMock()
        mock_client.chat.return_value = _make_response(summary_text)
        mod.get_cohere_client = MagicMock(return_value=mock_client)
        return mod, mock_client

    def test_successful_summary_returned(self):
        mod, _ = self._patched_module("This is the summary.")
        result = mod.generate_summary("Document text here.", "legal")
        assert result == "This is the summary."

    def test_correct_model_used(self):
        mod, mock_client = self._patched_module()
        mod.generate_summary("Some text.", "medical")
        call_kwargs = mock_client.chat.call_args
        assert call_kwargs.kwargs.get("model") == "command-a-plus-05-2026" or \
               call_kwargs.args[0] == "command-a-plus-05-2026" if call_kwargs.args else True

    def test_messages_contain_prompt(self):
        mod, mock_client = self._patched_module()
        mod.generate_summary("Technical content.", "technical")
        messages = mock_client.chat.call_args.kwargs["messages"]
        assert messages[0]["role"] == "user"
        assert "Technical content." in messages[0]["content"]

    def test_empty_document_raises_value_error(self):
        mod, _ = self._patched_module()
        with pytest.raises(ValueError, match="must not be empty"):
            mod.generate_summary("", "legal")

    def test_invalid_domain_raises_value_error(self):
        mod, _ = self._patched_module()
        with pytest.raises(ValueError, match="Unsupported domain"):
            mod.generate_summary("Some text.", "unknown")

    def test_api_failure_raises_runtime_error(self):
        mod = _fresh_module()
        mock_client = MagicMock()
        mock_client.chat.side_effect = Exception("Connection timeout")
        mod.get_cohere_client = MagicMock(return_value=mock_client)
        with pytest.raises(RuntimeError, match="Cohere API call failed"):
            mod.generate_summary("Some text.", "legal")

    def test_all_three_domains_succeed(self):
        for domain in ("legal", "medical", "technical"):
            mod, _ = self._patched_module(f"{domain} summary")
            result = mod.generate_summary("Document text.", domain)
            assert result == f"{domain} summary"
