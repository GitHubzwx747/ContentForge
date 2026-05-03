import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.model.provider import ChatResult
from src.orchestrator.langgraph_impl import LangGraphOrchestrator
from src.storage.models import PipelineState


def make_full_mock_provider():
    """Mock provider covering full pipeline flow."""
    responses = [
        # TrendInterpreter
        json.dumps({
            "core_event": "AI Agent技术爆发",
            "key_data": ["OpenAI发布GPT-5", "Anthropic发布Claude 4"],
            "sentiment": "期待",
            "angles": ["技术趋势", "职场影响", "创业机会"],
        }, ensure_ascii=False),
        # StrategyPlanner
        json.dumps({
            "xiaohongshu": {
                "angle": "职场效率革命",
                "audience": "25-35岁职场白领",
                "structure": {"hook": "痛点引入", "body": "案例+数据", "cta": "关注获取更多"},
                "emotion_hook": "焦虑→希望",
            },
        }, ensure_ascii=False),
        # ContentWriter
        "🔥 AI Agent到底有多强？实测后我惊了\n\n正文内容在这里...\n\n#AI #效率",
        # QualityReviewer
        json.dumps({"score": 92, "feedback": "标题吸引力强，内容结构清晰，建议增加具体数据"}, ensure_ascii=False),
        # FinalPolisher
        json.dumps({
            "final_content": "🔥 AI Agent到底有多强？实测后我惊了\n\n最终定稿内容...\n\n#AI #效率 #Agent",
            "title_options": [
                "AI Agent到底有多强？实测后我惊了",
                "用了AI Agent后，我的效率翻了3倍",
                "2026年了，你还没用AI Agent？",
            ],
        }, ensure_ascii=False),
    ]
    call_count = 0

    async def mock_chat(messages, **kwargs):
        nonlocal call_count
        content = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return ChatResult(content=content, input_tokens=200, output_tokens=100, total_tokens=300)

    provider = MagicMock()
    provider.chat = AsyncMock(side_effect=mock_chat)
    return provider


@pytest.mark.asyncio
async def test_full_pipeline_produces_complete_output():
    provider = make_full_mock_provider()
    orch = LangGraphOrchestrator(provider, prompt_dir="config/prompts", score_threshold=85, max_cycles=2)

    state = PipelineState(
        trend_markdown="# AI Agent爆发\n\nOpenAI发布GPT-5...",
        platforms=["xiaohongshu"],
    )
    result = await orch.invoke(state)

    # All pipeline stages completed
    assert result.trend_profile is not None
    assert result.trend_profile.core_event == "AI Agent技术爆发"
    assert "xiaohongshu" in result.strategies
    assert "xiaohongshu" in result.drafts
    assert "xiaohongshu" in result.review_scores
    assert result.review_scores["xiaohongshu"] == 92
    assert "xiaohongshu" in result.final_content
    assert len(result.title_options["xiaohongshu"]) == 3

    # Metrics populated
    assert result.metrics.total_tokens > 0
    assert result.metrics.total_duration > 0
    assert result.metrics.average_score == 92.0
    assert len(result.metrics.agents) == 5
