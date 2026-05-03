from dataclasses import dataclass

from openai import AsyncOpenAI

from src.storage.models import ModelSource


@dataclass
class ChatResult:
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


class ModelProvider:
    """Unified model call layer wrapping OpenAI-compatible APIs."""

    def __init__(self, source: ModelSource):
        self.source = source
        self.client = AsyncOpenAI(
            base_url=source.base_url,
            api_key=source.api_key,
        )

    async def chat(self, messages: list[dict], **kwargs) -> ChatResult:
        response = await self.client.chat.completions.create(
            model=self.source.model_name,
            messages=messages,
            **kwargs,
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        return ChatResult(
            content=content,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )
