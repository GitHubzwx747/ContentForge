# tests/test_models.py
from src.storage.models import (
    TrendProfile, PlatformStrategy, PipelineState,
    AgentMetrics, PipelineMetrics,
)


def test_trend_profile_creation():
    profile = TrendProfile(
        core_event="AI Agent爆发",
        key_data=["OpenAI发布GPT-5", "Anthropic发布Claude 4"],
        sentiment="期待",
        angles=["技术趋势", "职场影响", "创业机会"],
    )
    assert profile.core_event == "AI Agent爆发"
    assert len(profile.angles) == 3


def test_platform_strategy_creation():
    strategy = PlatformStrategy(
        angle="职场效率提升",
        audience="25-35岁职场白领",
        structure={"hook": "痛点引入", "body": "案例分析", "cta": "引导关注"},
        emotion_hook="焦虑→希望",
    )
    assert strategy.audience == "25-35岁职场白领"
    assert "hook" in strategy.structure


def test_pipeline_state_defaults():
    state = PipelineState(
        trend_markdown="# 热点\n内容",
        platforms=["xiaohongshu", "wechat"],
    )
    assert state.trend_profile is None
    assert state.strategies == {}
    assert state.drafts == {}
    assert state.review_scores == {}
    assert state.final_content == {}
    assert state.metrics.total_tokens == 0


def test_pipeline_metrics_defaults():
    metrics = PipelineMetrics()
    assert metrics.agents == []
    assert metrics.total_duration == 0.0
    assert metrics.total_tokens == 0
    assert metrics.average_score == 0.0
    assert metrics.review_cycles == 0


def test_agent_metrics_creation():
    m = AgentMetrics(
        agent_name="trend_interpreter",
        duration_seconds=1.2,
        input_tokens=500,
        output_tokens=300,
        total_tokens=800,
    )
    assert m.agent_name == "trend_interpreter"
    assert m.total_tokens == 800
