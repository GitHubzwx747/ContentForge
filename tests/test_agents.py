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


from src.agents.strategy_planner import StrategyPlanner
from src.storage.models import PlatformStrategy


@pytest.mark.asyncio
async def test_strategy_planner_creates_strategies():
    response = json.dumps({
        "xiaohongshu": {
            "angle": "职场效率",
            "audience": "25-35白领",
            "structure": {"hook": "痛点", "body": "案例", "cta": "关注"},
            "emotion_hook": "焦虑→希望",
        },
        "wechat": {
            "angle": "深度分析",
            "audience": "知识工作者",
            "structure": {"hook": "数据", "body": "论证", "cta": "思考"},
            "emotion_hook": "好奇→认同",
        },
    }, ensure_ascii=False)
    provider = mock_provider(response)
    agent = StrategyPlanner(provider, prompt_dir="config/prompts")

    state = PipelineState(
        trend_markdown="test",
        platforms=["xiaohongshu", "wechat"],
        trend_profile=TrendProfile(
            core_event="AI爆发",
            key_data=["GPT-5"],
            sentiment="期待",
            angles=["技术", "职场"],
        ),
    )
    result = await agent.run(state)

    assert "xiaohongshu" in result.strategies
    assert "wechat" in result.strategies
    assert result.strategies["xiaohongshu"].angle == "职场效率"
    assert result.metrics.agents[-1].agent_name == "strategy_planner"


from src.agents.content_writer import ContentWriter


@pytest.mark.asyncio
async def test_content_writer_creates_drafts():
    provider = mock_provider("# AI改变生活\n\n正文内容...")
    agent = ContentWriter(provider, prompt_dir="config/prompts")

    state = PipelineState(
        trend_markdown="test",
        platforms=["xiaohongshu"],
        strategies={
            "xiaohongshu": PlatformStrategy(
                angle="职场效率",
                audience="白领",
                structure={"hook": "痛点", "body": "案例", "cta": "关注"},
                emotion_hook="焦虑→希望",
            ),
        },
    )
    result = await agent.run(state)

    assert "xiaohongshu" in result.drafts
    assert "正文内容" in result.drafts["xiaohongshu"]
    assert result.metrics.agents[-1].agent_name == "content_writer"


from src.agents.quality_reviewer import QualityReviewer


@pytest.mark.asyncio
async def test_quality_reviewer_scores_drafts():
    response = json.dumps({"score": 92, "feedback": "整体不错，标题可以更吸引人"}, ensure_ascii=False)
    provider = mock_provider(response)
    agent = QualityReviewer(provider, prompt_dir="config/prompts")

    state = PipelineState(
        trend_markdown="test",
        platforms=["xiaohongshu"],
        drafts={"xiaohongshu": "# 标题\n正文内容"},
    )
    result = await agent.run(state)

    assert result.review_scores["xiaohongshu"] == 92
    assert "不错" in result.review_feedback["xiaohongshu"]
    assert result.metrics.agents[-1].agent_name == "quality_reviewer"


from src.agents.final_polisher import FinalPolisher


@pytest.mark.asyncio
async def test_final_polisher_produces_final_content():
    response = json.dumps({
        "final_content": "# 最终标题\n\n最终正文内容 #标签",
        "title_options": ["标题A", "标题B", "标题C"],
    }, ensure_ascii=False)
    provider = mock_provider(response)
    agent = FinalPolisher(provider, prompt_dir="config/prompts")

    state = PipelineState(
        trend_markdown="test",
        platforms=["xiaohongshu"],
        drafts={"xiaohongshu": "# 初稿\n正文"},
        review_feedback={"xiaohongshu": "需要改进"},
        review_scores={"xiaohongshu": 88},
    )
    result = await agent.run(state)

    assert "xiaohongshu" in result.final_content
    assert "最终" in result.final_content["xiaohongshu"]
    assert len(result.title_options["xiaohongshu"]) == 3
    assert result.metrics.agents[-1].agent_name == "final_polisher"
