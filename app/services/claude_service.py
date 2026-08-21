from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel, ValidationError

from app.config import get_settings


class ClaudeConfigurationError(RuntimeError):
    pass


class ClaudeResponseError(RuntimeError):
    pass


@dataclass(frozen=True)
class ClaudeTextResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


StructuredModel = TypeVar(
    "StructuredModel",
    bound=BaseModel,
)


@dataclass(frozen=True)
class ClaudeStructuredResult(Generic[StructuredModel]):
    data: StructuredModel
    model: str
    input_tokens: int
    output_tokens: int


class ClaudeService:
    # Low-level wrapper around the Anthropic Messages API.

    def __init__(self) -> None:
        settings = get_settings()

        if settings.anthropic_api_key is None:
            raise ClaudeConfigurationError(
                "ANTHROPIC_API_KEY is not configured."
            )

        api_key = settings.anthropic_api_key.get_secret_value().strip()
        if not api_key:
            raise ClaudeConfigurationError(
                "ANTHROPIC_API_KEY is empty."
            )

        if not settings.claude_model:
            raise ClaudeConfigurationError(
                "CLAUDE_MODEL is not configured."
            )

        self.model = settings.claude_model
        self.client = AsyncAnthropic(
            api_key=api_key,
            timeout=settings.claude_timeout_seconds,
            max_retries=settings.claude_max_retries,
        )

    async def generate_text(
        self,
        user_message: str,
        *,
        max_tokens: int = 300,
        system: str | None = None,
    ) -> ClaudeTextResult:
        request = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
        }

        if system:
            request["system"] = system

        message = await self.client.messages.create(**request)

        text_parts = [
            block.text
            for block in message.content
            if block.type == "text"
        ]
        text = "\n".join(text_parts).strip()

        return ClaudeTextResult(
            text=text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    async def generate_structured(
        self,
        user_message: str,
        *,
        output_model: type[StructuredModel],
        max_tokens: int = 500,
        system: str | None = None,
    ) -> ClaudeStructuredResult[StructuredModel]:
        request = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            "output_format": output_model,
        }

        if system:
            request["system"] = system

        try:
            message = await self.client.messages.parse(**request)
        except ValidationError as exc:
            raise ClaudeResponseError(
                "Claude structured output failed application validation."
            ) from exc

        if message.parsed_output is None:
            raise ClaudeResponseError(
                "Claude returned no parsed structured output."
            )

        return ClaudeStructuredResult(
            data=message.parsed_output,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    async def create_message(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int = 600,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system:
            request["system"] = system

        if tools:
            request["tools"] = tools

        return await self.client.messages.create(**request)

    async def close(self) -> None:
        await self.client.close()
