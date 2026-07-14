import logging
from typing import Any, ClassVar

import httpx
from groq import RateLimitError
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_groq import ChatGroq
from pydantic import SecretStr

logger = logging.getLogger(__name__)

class RotationalChatGroq(ChatGroq):
    _current_key_idx: ClassVar[int] = 0
    _keys: ClassVar[list[str]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from src.config.settings import settings

        # Load keys from settings if they haven't been loaded yet
        if not RotationalChatGroq._keys:
            RotationalChatGroq._keys = settings.groq_keys

        # Fallback to the provided api_key if no keys are found in settings
        if not RotationalChatGroq._keys:
            api_key = kwargs.get("api_key") or kwargs.get("groq_api_key")
            if api_key:
                if isinstance(api_key, SecretStr):
                    RotationalChatGroq._keys = [api_key.get_secret_value()]
                else:
                    RotationalChatGroq._keys = [str(api_key)]

        # Apply the active key
        active_idx = RotationalChatGroq._current_key_idx
        if RotationalChatGroq._keys:
            active_idx = active_idx % len(RotationalChatGroq._keys)
            kwargs["api_key"] = RotationalChatGroq._keys[active_idx]

        super().__init__(*args, **kwargs)

    def _sync_client_to_active_key(self) -> None:
        if not RotationalChatGroq._keys:
            return

        active_idx = RotationalChatGroq._current_key_idx % len(RotationalChatGroq._keys)
        active_key = RotationalChatGroq._keys[active_idx]

        # Recreate client credentials if key changed
        if not self.groq_api_key or self.groq_api_key.get_secret_value() != active_key:
            self.groq_api_key = SecretStr(active_key)
            self.client = None
            self.async_client = None
            self.validate_environment()  # type: ignore[operator]

        print(f"Using Groq key {active_idx + 1}/{len(RotationalChatGroq._keys)}.")
        logger.info(f"Using Groq key {active_idx + 1}/{len(RotationalChatGroq._keys)}.")

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Ensure we are synchronized to the active key
        self._sync_client_to_active_key()

        num_keys = len(RotationalChatGroq._keys)
        if num_keys <= 1:
            return super()._generate(messages, stop, run_manager, **kwargs)

        attempts = 0
        while attempts < num_keys:
            active_idx = RotationalChatGroq._current_key_idx % num_keys
            try:
                res = super()._generate(messages, stop, run_manager, **kwargs)
                print(
                    "Groq request succeeded using key "
                    f"{active_idx + 1}/{num_keys}."
                )
                logger.info(
                    "Groq request succeeded using key "
                    f"{active_idx + 1}/{num_keys}."
                )
                return res
            except RateLimitError:
                print(f"Groq key {active_idx + 1}/{num_keys} exhausted.\n")
                logger.warning(f"Groq key {active_idx + 1}/{num_keys} exhausted.")

                # Switch to the next key index
                RotationalChatGroq._current_key_idx = (active_idx + 1) % num_keys
                print(
                    "Switching to key "
                    f"{RotationalChatGroq._current_key_idx + 1}/{num_keys}."
                )
                logger.warning(
                    "Switching to key "
                    f"{RotationalChatGroq._current_key_idx + 1}/{num_keys}."
                )

                # Re-sync client to new key index
                self._sync_client_to_active_key()
                attempts += 1

        print("All configured Groq API keys are currently rate limited.")
        logger.error("All configured Groq API keys are currently rate limited.")
        dummy_request = httpx.Request("POST", "https://api.groq.com")
        dummy_response = httpx.Response(429, request=dummy_request)
        raise RateLimitError(
            "All configured Groq API keys are currently rate limited.",
            response=dummy_response,
            body=None
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Ensure we are synchronized to the active key
        self._sync_client_to_active_key()

        num_keys = len(RotationalChatGroq._keys)
        if num_keys <= 1:
            return await super()._agenerate(messages, stop, run_manager, **kwargs)

        attempts = 0
        while attempts < num_keys:
            active_idx = RotationalChatGroq._current_key_idx % num_keys
            try:
                res = await super()._agenerate(messages, stop, run_manager, **kwargs)
                print(
                    "Groq request succeeded using key "
                    f"{active_idx + 1}/{num_keys}."
                )
                logger.info(
                    "Groq request succeeded using key "
                    f"{active_idx + 1}/{num_keys}."
                )
                return res
            except RateLimitError:
                print(f"Groq key {active_idx + 1}/{num_keys} exhausted.\n")
                logger.warning(f"Groq key {active_idx + 1}/{num_keys} exhausted.")

                # Switch to the next key index
                RotationalChatGroq._current_key_idx = (active_idx + 1) % num_keys
                print(
                    "Switching to key "
                    f"{RotationalChatGroq._current_key_idx + 1}/{num_keys}."
                )
                logger.warning(
                    "Switching to key "
                    f"{RotationalChatGroq._current_key_idx + 1}/{num_keys}."
                )

                # Re-sync client to new key index
                self._sync_client_to_active_key()
                attempts += 1

        print("All configured Groq API keys are currently rate limited.")
        logger.error("All configured Groq API keys are currently rate limited.")
        dummy_request = httpx.Request("POST", "https://api.groq.com")
        dummy_response = httpx.Response(429, request=dummy_request)
        raise RateLimitError(
            "All configured Groq API keys are currently rate limited.",
            response=dummy_response,
            body=None
        )
