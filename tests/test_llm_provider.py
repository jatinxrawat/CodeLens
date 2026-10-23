"""Unit tests for LLMProvider layer (GeminiProvider, LocalProvider, ProviderManager)."""

import pytest
from unittest.mock import MagicMock, patch
from app.reasoning.provider.base import LLMProvider
from app.reasoning.provider.gemini_provider import GeminiProvider
from app.reasoning.provider.local_provider import LocalProvider
from app.reasoning.provider.manager import ProviderManager


def test_provider_manager_initialization():
    mgr = ProviderManager()
    assert mgr.active_provider_name in ("gemini", "local")
    status = mgr.get_provider_status()
    assert "active_provider" in status
    assert "gemini_flash_model" in status
    assert "gemini_pro_model" in status
    assert "local_model" in status


def test_provider_manager_switch():
    mgr = ProviderManager()
    local_p = mgr.set_active_provider("local")
    assert mgr.active_provider_name == "local"
    assert isinstance(local_p, LocalProvider)

    # Invalid provider should raise ValueError
    with pytest.raises(ValueError):
        mgr.set_active_provider("invalid_provider")


def test_local_provider_generate_and_citations():
    provider = LocalProvider()
    assert provider.provider_name == "local"

    # Test prompt without context
    ans = provider.generate("What is quicksort?")
    assert len(ans) > 0
    assert "quicksort" in ans.lower()

    # Test prompt with context citing files
    ctx = "File: auth/login.py (L10-25)\ndef login(user, pw):\n    return check_password(user, pw)"
    ans_ctx = provider.generate("Where is authentication handled?", context=ctx)
    assert len(ans_ctx) > 0


def test_local_provider_generate_json():
    provider = LocalProvider()
    schema = {"type": "object", "properties": {"difficulty": {"type": "string"}}}
    res = provider.generate_json("Analyze issue #42: add typing hints", schema=schema)
    assert isinstance(res, dict)
    assert "difficulty" in res
    assert "skills" in res


def test_gemini_provider_mock_generate():
    provider = GeminiProvider(api_key="mock_test_key_12345")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Here is the explanation with citations: [app/main.py:L10-20]."
    mock_client.models.generate_content.return_value = mock_response

    provider._client = mock_client

    ans = provider.generate("Explain the main function", model_tier="flash")
    assert ans == "Here is the explanation with citations: [app/main.py:L10-20]."
    assert mock_client.models.generate_content.called


def test_gemini_provider_mock_embed():
    provider = GeminiProvider(api_key="mock_test_key_12345")
    mock_client = MagicMock()
    
    mock_item = MagicMock()
    mock_item.values = [0.1] * 768
    mock_embed_resp = MagicMock()
    mock_embed_resp.embeddings = [mock_item]
    mock_client.models.embed_content.return_value = mock_embed_resp

    provider._client = mock_client

    vecs = provider.embed(["def search_code(): pass"])
    assert len(vecs) == 1
    assert len(vecs[0]) == 768


def test_gemini_provider_mock_generate_json():
    provider = GeminiProvider(api_key="mock_test_key_12345")
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = '{"difficulty": "easy", "skills": ["python", "ast"], "likely_files": ["app/parser.py"], "summary": "Fix parsing issue"}'
    mock_client.models.generate_content.return_value = mock_resp

    provider._client = mock_client

    schema = {
        "type": "object",
        "properties": {
            "difficulty": {"type": "string"},
            "skills": {"type": "array"},
        },
    }
    data = provider.generate_json("Assess this issue", schema=schema)
    assert data["difficulty"] == "easy"
    assert "python" in data["skills"]
    assert "app/parser.py" in data["likely_files"]
