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
    _key_cooldowns: ClassVar[list[float]] = []
    _rate_limit_count: ClassVar[int] = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from src.config.settings import settings

        # Load keys from settings if they haven't been loaded yet
        if not RotationalChatGroq._keys:
            RotationalChatGroq._keys = settings.groq_keys
            RotationalChatGroq._key_cooldowns = [0.0] * len(RotationalChatGroq._keys)

        # Fallback to the provided api_key if no keys are found in settings
        if not RotationalChatGroq._keys:
            api_key = kwargs.get("api_key") or kwargs.get("groq_api_key")
            if api_key:
                if isinstance(api_key, SecretStr):
                    RotationalChatGroq._keys = [api_key.get_secret_value()]
                else:
                    RotationalChatGroq._keys = [str(api_key)]
                RotationalChatGroq._key_cooldowns = [0.0] * len(RotationalChatGroq._keys)

        # Apply the active key
        active_idx = RotationalChatGroq._current_key_idx
        if RotationalChatGroq._keys:
            if len(RotationalChatGroq._key_cooldowns) != len(RotationalChatGroq._keys):
                RotationalChatGroq._key_cooldowns = [0.0] * len(RotationalChatGroq._keys)

            import time
            selected_idx = -1
            num_keys = len(RotationalChatGroq._keys)
            for step in range(num_keys):
                candidate_idx = (active_idx + step) % num_keys
                if time.time() >= RotationalChatGroq._key_cooldowns[candidate_idx]:
                    selected_idx = candidate_idx
                    break
            
            if selected_idx == -1:
                # Fallback: choose the key with the smallest cooldown timestamp
                selected_idx = min(range(num_keys), key=lambda idx: RotationalChatGroq._key_cooldowns[idx])

            RotationalChatGroq._current_key_idx = selected_idx
            kwargs["api_key"] = RotationalChatGroq._keys[selected_idx]

        super().__init__(*args, **kwargs)

    def _get_cooldown_from_error(self, exc: RateLimitError) -> float:
        from src.config.settings import settings
        default_cooldown = getattr(settings, "GROQ_DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS", 10.0)
        if not exc.response or not hasattr(exc.response, "headers"):
            return default_cooldown
        
        headers = exc.response.headers
        
        # 1. Try "retry-after"
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
                
        # 2. Try "x-ratelimit-reset-tokens"
        reset_tokens = headers.get("x-ratelimit-reset-tokens")
        if reset_tokens:
            reset_tokens = reset_tokens.strip().lower()
            try:
                if reset_tokens.endswith("ms"):
                    return float(reset_tokens[:-2]) / 1000.0
                elif reset_tokens.endswith("s"):
                    return float(reset_tokens[:-1])
                else:
                    return float(reset_tokens)
            except ValueError:
                pass
                
        return default_cooldown

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
            except RateLimitError as exc:
                print(f"Groq key {active_idx + 1}/{num_keys} exhausted.\n")
                logger.warning(f"Groq key {active_idx + 1}/{num_keys} exhausted.")

                # Increment the rate limit count
                RotationalChatGroq._rate_limit_count += 1

                # Set cooldown for the current key
                import time
                cooldown = self._get_cooldown_from_error(exc)
                RotationalChatGroq._key_cooldowns[active_idx] = time.time() + cooldown

                # Find the next available key starting from (active_idx + 1)
                selected_idx = -1
                for step in range(num_keys):
                    candidate_idx = (active_idx + 1 + step) % num_keys
                    if time.time() >= RotationalChatGroq._key_cooldowns[candidate_idx]:
                        selected_idx = candidate_idx
                        break
                if selected_idx == -1:
                    selected_idx = min(range(num_keys), key=lambda idx: RotationalChatGroq._key_cooldowns[idx])

                RotationalChatGroq._current_key_idx = selected_idx
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
            except RateLimitError as exc:
                print(f"Groq key {active_idx + 1}/{num_keys} exhausted.\n")
                logger.warning(f"Groq key {active_idx + 1}/{num_keys} exhausted.")

                # Increment the rate limit count
                RotationalChatGroq._rate_limit_count += 1

                # Set cooldown for the current key
                import time
                cooldown = self._get_cooldown_from_error(exc)
                RotationalChatGroq._key_cooldowns[active_idx] = time.time() + cooldown

                # Find the next available key starting from (active_idx + 1)
                selected_idx = -1
                for step in range(num_keys):
                    candidate_idx = (active_idx + 1 + step) % num_keys
                    if time.time() >= RotationalChatGroq._key_cooldowns[candidate_idx]:
                        selected_idx = candidate_idx
                        break
                if selected_idx == -1:
                    selected_idx = min(range(num_keys), key=lambda idx: RotationalChatGroq._key_cooldowns[idx])

                RotationalChatGroq._current_key_idx = selected_idx
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
