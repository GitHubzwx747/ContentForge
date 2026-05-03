import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.orchestrator.langgraph_impl import LangGraphOrchestrator
from src.model.provider import ChatResult
from src.storage.models import PipelineState


def make_mock_provider():
    """Create a mock provider that returns valid JSON for each agent."""
    call_count = 0

    responses = [
        # Agent 1: TrendInterpreter
        json.dumps({"core_event": "AI爆发", "key_data": ["GPT-5"], "sentiment": "期待", "angles": ["技术"]}, ensure_ascii=False),
        # Agent 2: StrategyPlanner
        json.dumps({"xiaohongshu": {"angle": "效率", "audience": "白领", "structure": {"hook": "h", "body": "b", "cta": "c"}, "emotion_hook": "e"}}, ensure_ascii=False),
        # Agent 3: ContentWriter
        "# 小红书文案\n\n正文内容",
        # Agent 4: QualityReviewer
        json.dumps({"score": 90, "feedback": "不错"}, ensure_ascii=False),
        # Agent 5: FinalPolisher
        json.dumps({"final_content": "# 最终文案\n\n定稿", "title_options": ["标题1", "标题2", "标题3"]}, ensure_ascii=False),
    ]

    async def mock_chat(messages, **kwargs):
        nonlocal call_count
        content = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return ChatResult(content=content, input_tokens=100, output_tokens=50, total_tokens=150)

    provider = MagicMock()
    provider.chat = AsyncMock(side_effect=mock_chat)
    return provider


@pytest.mark.asyncio
async def test_orchestrator_runs_full_pipeline():
    provider = make_mock_provider()
    orch = LangGraphOrchestrator(provider, prompt_dir="config/prompts", score_threshold=85, max_cycles=2)

    state = PipelineState(
        trend_markdown="# AI Agent爆发\n内容...",
        platforms=["xiaohongshu"],
    )
    result = await orch.invoke(state)

    assert result.trend_profile is not None
    assert "xiaohongshu" in result.strategies
    assert "xiaohongshu" in result.drafts
    assert "xiaohongshu" in result.review_scores
    assert "xiaohongshu" in result.final_content
    assert len(result.title_options["xiaohongshu"]) == 3
    assert len(result.metrics.agents) == 5
