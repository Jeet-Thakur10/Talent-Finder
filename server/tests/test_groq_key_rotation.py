import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from groq import RateLimitError
import httpx
from langchain_core.messages import HumanMessage
from src.control.agents.groq_client import RotationalChatGroq

class MockSettings:
    @property
    def groq_keys(self) -> list[str]:
        return ["KEY1", "KEY2", "KEY3"]

@pytest.fixture(autouse=True)
def mock_settings():
    with patch("src.config.settings.settings", MockSettings()) as mocked:
        yield mocked

def test_sync_rotation_succeeds_on_second_key():
    # Reset ClassVars
    RotationalChatGroq._current_key_idx = 0
    RotationalChatGroq._keys = []

    # Instantiate client
    client = RotationalChatGroq(model="llama-3.3-70b-versatile")
    assert RotationalChatGroq._keys == ["KEY1", "KEY2", "KEY3"]

    dummy_request = httpx.Request("POST", "https://api.groq.com")
    dummy_response = httpx.Response(429, request=dummy_request)
    rate_limit_err = RateLimitError("Rate limit exceeded", response=dummy_response, body=None)

    success_result = MagicMock()

    call_count = 0
    def mock_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        active_key = client.groq_api_key.get_secret_value()
        if active_key == "KEY1":
            raise rate_limit_err
        return success_result

    with patch("langchain_groq.ChatGroq._generate", side_effect=mock_generate):
        res = client._generate([HumanMessage(content="test")])
        assert res == success_result
        assert call_count == 2
        # KEY2 is index 1
        assert RotationalChatGroq._current_key_idx == 1

@pytest.mark.asyncio
async def test_async_rotation_succeeds_on_second_key():
    RotationalChatGroq._current_key_idx = 0
    RotationalChatGroq._keys = []

    client = RotationalChatGroq(model="llama-3.3-70b-versatile")

    dummy_request = httpx.Request("POST", "https://api.groq.com")
    dummy_response = httpx.Response(429, request=dummy_request)
    rate_limit_err = RateLimitError("Rate limit exceeded", response=dummy_response, body=None)

    success_result = MagicMock()

    call_count = 0
    async def mock_agenerate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        active_key = client.groq_api_key.get_secret_value()
        if active_key == "KEY1":
            raise rate_limit_err
        return success_result

    with patch("langchain_groq.ChatGroq._agenerate", side_effect=mock_agenerate):
        res = await client._agenerate([HumanMessage(content="test")])
        assert res == success_result
        assert call_count == 2
        assert RotationalChatGroq._current_key_idx == 1

def test_all_keys_exhausted():
    RotationalChatGroq._current_key_idx = 0
    RotationalChatGroq._keys = []

    client = RotationalChatGroq(model="llama-3.3-70b-versatile")

    dummy_request = httpx.Request("POST", "https://api.groq.com")
    dummy_response = httpx.Response(429, request=dummy_request)
    rate_limit_err = RateLimitError("Rate limit exceeded", response=dummy_response, body=None)

    call_count = 0
    def mock_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise rate_limit_err

    with patch("langchain_groq.ChatGroq._generate", side_effect=mock_generate):
        with pytest.raises(RateLimitError) as exc_info:
            client._generate([HumanMessage(content="test")])
        assert "All configured Groq API keys are currently rate limited" in str(exc_info.value)
        # Should have tried all 3 keys
        assert call_count == 3
        # wrapped around 3 % 3 = 0
        assert RotationalChatGroq._current_key_idx == 0

def test_other_exceptions_not_retried():
    RotationalChatGroq._current_key_idx = 0
    RotationalChatGroq._keys = []

    client = RotationalChatGroq(model="llama-3.3-70b-versatile")

    call_count = 0
    def mock_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise ValueError("Invalid request params")

    with patch("langchain_groq.ChatGroq._generate", side_effect=mock_generate):
        with pytest.raises(ValueError) as exc_info:
            client._generate([HumanMessage(content="test")])
        assert "Invalid request params" in str(exc_info.value)
        # Should fail immediately on first try
        assert call_count == 1
        assert RotationalChatGroq._current_key_idx == 0

def test_key_cooldown_header_parsing():
    RotationalChatGroq._current_key_idx = 0
    RotationalChatGroq._keys = []
    
    client = RotationalChatGroq(model="llama-3.3-70b-versatile")
    
    # 1. Test standard headers
    dummy_request = httpx.Request("POST", "https://api.groq.com")
    dummy_headers = httpx.Headers({"retry-after": "15.0"})
    dummy_response = httpx.Response(429, request=dummy_request, headers=dummy_headers)
    rate_limit_err = RateLimitError("Rate limit exceeded", response=dummy_response, body=None)
    
    cooldown = client._get_cooldown_from_error(rate_limit_err)
    assert cooldown == 15.0
    
    # 2. Test x-ratelimit-reset-tokens with 's' suffix
    dummy_headers_s = httpx.Headers({"x-ratelimit-reset-tokens": "2.5s"})
    dummy_response_s = httpx.Response(429, request=dummy_request, headers=dummy_headers_s)
    rate_limit_err_s = RateLimitError("Rate limit exceeded", response=dummy_response_s, body=None)
    cooldown_s = client._get_cooldown_from_error(rate_limit_err_s)
    assert cooldown_s == 2.5
    
    # 3. Test x-ratelimit-reset-tokens with 'ms' suffix
    dummy_headers_ms = httpx.Headers({"x-ratelimit-reset-tokens": "500ms"})
    dummy_response_ms = httpx.Response(429, request=dummy_request, headers=dummy_headers_ms)
    rate_limit_err_ms = RateLimitError("Rate limit exceeded", response=dummy_response_ms, body=None)
    cooldown_ms = client._get_cooldown_from_error(rate_limit_err_ms)
    assert cooldown_ms == 0.5
