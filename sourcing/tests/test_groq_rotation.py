import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
from groq import RateLimitError

from src.config.settings import Settings
from src.control.agents.groq_client import RotationalChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# Mock the internal LangChain chat result helper to avoid index issues with mock responses
def mock_create_chat_result(self, response, params):
    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response.choices[0].message.content))])

def test_settings_groq_keys_merging():
    print("Running test_settings_groq_keys_merging...")
    settings = Settings(
        GROQ_API_KEYS="key3, key4",
        DATABASE_URL="sqlite:///:memory:",
        SECRET_KEY="test"
    )
    assert settings.groq_keys == ["key3", "key4"], f"Expected ['key3', 'key4'], got {settings.groq_keys}"

    settings_empty = Settings(
        GROQ_API_KEYS="",
        DATABASE_URL="sqlite:///:memory:",
        SECRET_KEY="test"
    )
    assert settings_empty.groq_keys == [], f"Expected [], got {settings_empty.groq_keys}"
    print("Passed.")

@patch("langchain_groq.ChatGroq._create_chat_result", mock_create_chat_result)
def test_rotational_client_normal_flow():
    print("Running test_rotational_client_normal_flow...")
    dummy_response = MagicMock()
    dummy_response.choices = [
        MagicMock(message=MagicMock(content="Mock Success"), finish_reason="stop")
    ]
    dummy_response.usage = MagicMock(prompt_tokens=5, completion_tokens=5, total_tokens=10)

    mock_groq = MagicMock()
    mock_groq.chat.completions.create.return_value = dummy_response

    # Force keys list and index
    RotationalChatGroq._keys = ["key_a", "key_b"]
    RotationalChatGroq._current_key_idx = 0

    with patch("groq.Groq", return_value=mock_groq):
        llm = RotationalChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        res = llm.invoke([HumanMessage(content="test")])
        assert res.content == "Mock Success"
        assert RotationalChatGroq._current_key_idx == 0
        assert llm.groq_api_key.get_secret_value() == "key_a"
    print("Passed.")

@patch("langchain_groq.ChatGroq._create_chat_result", mock_create_chat_result)
def test_rotational_client_rotates_and_persists():
    print("Running test_rotational_client_rotates_and_persists...")
    dummy_request = httpx.Request("POST", "https://api.groq.com")
    dummy_response_429 = httpx.Response(429, request=dummy_request)
    rate_limit_err = RateLimitError("Rate limited key", response=dummy_response_429, body=None)

    dummy_success = MagicMock()
    dummy_success.choices = [
        MagicMock(message=MagicMock(content="Mock Success Key B"), finish_reason="stop")
    ]
    dummy_success.usage = MagicMock(prompt_tokens=5, completion_tokens=5, total_tokens=10)

    # Mock completions.create to fail on key_a and succeed on key_b
    def mock_create(*args, **kwargs):
        idx = RotationalChatGroq._current_key_idx
        current_key = RotationalChatGroq._keys[idx]
        if current_key == "key_a":
            raise rate_limit_err
        elif current_key == "key_b":
            return dummy_success
        raise Exception("Unexpected key")

    mock_groq = MagicMock()
    mock_groq.chat.completions.create.side_effect = mock_create

    RotationalChatGroq._keys = ["key_a", "key_b"]
    RotationalChatGroq._current_key_idx = 0

    with patch("groq.Groq", return_value=mock_groq):
        llm = RotationalChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        res = llm.invoke([HumanMessage(content="test")])
        assert res.content == "Mock Success Key B"
        # Key should have rotated to key_b (idx = 1)
        assert RotationalChatGroq._current_key_idx == 1
        assert llm.groq_api_key.get_secret_value() == "key_b"

        # Subsequent call should use key_b directly without attempting key_a
        def mock_create_strict(*args, **kwargs):
            idx = RotationalChatGroq._current_key_idx
            current_key = RotationalChatGroq._keys[idx]
            if current_key == "key_a":
                raise Exception("Error: key_a was tried but we should stay on key_b!")
            return dummy_success

        mock_groq.chat.completions.create.side_effect = mock_create_strict
        
        res2 = llm.invoke([HumanMessage(content="test2")])
        assert res2.content == "Mock Success Key B"
        assert RotationalChatGroq._current_key_idx == 1
    print("Passed.")

@patch("langchain_groq.ChatGroq._create_chat_result", mock_create_chat_result)
def test_rotational_client_all_keys_exhausted():
    print("Running test_rotational_client_all_keys_exhausted...")
    dummy_request = httpx.Request("POST", "https://api.groq.com")
    dummy_response_429 = httpx.Response(429, request=dummy_request)
    rate_limit_err = RateLimitError("Rate limited", response=dummy_response_429, body=None)

    mock_groq = MagicMock()
    mock_groq.chat.completions.create.side_effect = rate_limit_err

    RotationalChatGroq._keys = ["key_a", "key_b"]
    RotationalChatGroq._current_key_idx = 0

    with patch("groq.Groq", return_value=mock_groq):
        llm = RotationalChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        raised = False
        try:
            llm.invoke([HumanMessage(content="test")])
        except RateLimitError as exc:
            assert "All configured Groq API keys are currently rate limited." in str(exc)
            raised = True
        assert raised, "Expected RateLimitError to be raised"
    print("Passed.")

@pytest.mark.asyncio
@patch("langchain_groq.ChatGroq._create_chat_result", mock_create_chat_result)
async def test_async_rotational_client_rotates_and_persists():
    print("Running test_async_rotational_client_rotates_and_persists...")
    dummy_request = httpx.Request("POST", "https://api.groq.com")
    dummy_response_429 = httpx.Response(429, request=dummy_request)
    rate_limit_err = RateLimitError("Rate limited key", response=dummy_response_429, body=None)

    dummy_success = MagicMock()
    dummy_success.choices = [
        MagicMock(message=MagicMock(content="Mock Success Key B Async"), finish_reason="stop")
    ]
    dummy_success.usage = MagicMock(prompt_tokens=5, completion_tokens=5, total_tokens=10)

    # Mock async completion
    async def mock_acreate(*args, **kwargs):
        idx = RotationalChatGroq._current_key_idx
        current_key = RotationalChatGroq._keys[idx]
        if current_key == "key_a":
            raise rate_limit_err
        elif current_key == "key_b":
            return dummy_success
        raise Exception("Unexpected key")

    mock_groq = MagicMock()
    mock_groq.chat.completions.create = AsyncMock(side_effect=mock_acreate)

    RotationalChatGroq._keys = ["key_a", "key_b"]
    RotationalChatGroq._current_key_idx = 0

    with patch("groq.AsyncGroq", return_value=mock_groq):
        llm = RotationalChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        res = await llm.ainvoke([HumanMessage(content="test")])
        assert res.content == "Mock Success Key B Async"
        # Key should have rotated to key_b (idx = 1)
        assert RotationalChatGroq._current_key_idx == 1
        assert llm.groq_api_key.get_secret_value() == "key_b"

        # Subsequent call should use key_b directly without attempting key_a
        async def mock_acreate_strict(*args, **kwargs):
            idx = RotationalChatGroq._current_key_idx
            current_key = RotationalChatGroq._keys[idx]
            if current_key == "key_a":
                raise Exception("Error: key_a was tried but we should stay on key_b!")
            return dummy_success

        mock_groq.chat.completions.create = AsyncMock(side_effect=mock_acreate_strict)
        
        res2 = await llm.ainvoke([HumanMessage(content="test2")])
        assert res2.content == "Mock Success Key B Async"
        assert RotationalChatGroq._current_key_idx == 1
    print("Passed.")

async def main():
    test_settings_groq_keys_merging()
    test_rotational_client_normal_flow()
    test_rotational_client_rotates_and_persists()
    test_rotational_client_all_keys_exhausted()
    await test_async_rotational_client_rotates_and_persists()
    print("\nALL ROTATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
