from unittest.mock import AsyncMock, MagicMock
import pytest
from src.model.provider import ModelProvider
from src.storage.models import ModelSource


def make_provider():
    source = ModelSource(
        name="test",
        base_url="http://localhost",
        api_key="sk-test",
        model_name="test-model",
    )
    return ModelProvider(source)


@pytest.mark.asyncio
async def test_chat_returns_content():
    provider = make_provider()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Hello world"))]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await provider.chat([{"role": "user", "content": "hi"}])
    assert result.content == "Hello world"
    assert result.input_tokens == 10
    assert result.output_tokens == 5


@pytest.mark.asyncio
async def test_chat_passes_model_and_messages():
    provider = make_provider()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_response.usage = MagicMock(prompt_tokens=5, completion_tokens=2, total_tokens=7)
    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    messages = [{"role": "system", "content": "you are helpful"}, {"role": "user", "content": "test"}]
    await provider.chat(messages)

    provider.client.chat.completions.create.assert_called_once()
    call_kwargs = provider.client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "test-model"
    assert call_kwargs.kwargs["messages"] == messages
