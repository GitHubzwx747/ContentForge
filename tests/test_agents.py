import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agents.trend_interpreter import TrendInterpreter
from src.model.provider import ChatResult
from src.storage.models import PipelineState, TrendProfile


def mock_provider(response_content: str):
    """Create a mock ModelProvider that returns given content."""
    provider = MagicMock()
    provider.chat = AsyncMock(return_value=ChatResult(
        content=response_content,
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
    ))
    return provider


@pytest.mark.asyncio
async def test_trend_interpreter_parses_json():
    response = json.dumps({
        "core_event": "AI Agent爆发",
        "key_data": ["GPT-5发布"],
        "sentiment": "期待",
        "angles": ["技术趋势", "职场影响", "创业机会"],
    }, ensure_ascii=False)
    provider = mock_provider(response)
    agent = TrendInterpreter(provider, prompt_dir="config/prompts")

    state = PipelineState(trend_markdown="# AI Agent爆发\n内容...")
    result = await agent.run(state)

    assert result.trend_profile is not None
    assert result.trend_profile.core_event == "AI Agent爆发"
    assert result.trend_profile.sentiment == "期待"
    assert len(result.trend_profile.angles) == 3
    assert result.metrics.agents[0].agent_name == "trend_interpreter"
    assert result.metrics.agents[0].total_tokens == 150


@pytest.mark.asyncio
async def test_trend_interpreter_handles_json_with_markdown_fence():
    raw = '```json\n{"core_event":"test","key_data":[],"sentiment":"正面","angles":["a"]}\n```'
    provider = mock_provider(raw)
    agent = TrendInterpreter(provider, prompt_dir="config/prompts")

    state = PipelineState(trend_markdown="test")
    result = await agent.run(state)

    assert result.trend_profile is not None
    assert result.trend_profile.core_event == "test"
