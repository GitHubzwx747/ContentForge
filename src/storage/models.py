from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class TrendProfile(BaseModel):
    """Agent 1 output: structured trend analysis."""
    core_event: str
    key_data: list[str] = Field(default_factory=list)
    sentiment: str  # 正面/争议/焦虑/期待
    angles: list[str] = Field(default_factory=list)


class PlatformStrategy(BaseModel):
    """Agent 2 output: per-platform content strategy."""
    angle: str
    audience: str
    structure: dict[str, str] = Field(default_factory=dict)  # hook/body/cta
    emotion_hook: str


class AgentMetrics(BaseModel):
    """Metrics for a single agent run."""
    agent_name: str
    duration_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class PipelineMetrics(BaseModel):
    """Aggregate pipeline run metrics."""
    agents: list[AgentMetrics] = Field(default_factory=list)
    total_duration: float = 0.0
    total_tokens: int = 0
    average_score: float = 0.0
    review_cycles: int = 0


class PipelineState(BaseModel):
    """Shared state flowing through the agent pipeline."""
    # Input
    trend_markdown: str
    platforms: list[str] = Field(default_factory=lambda: ["xiaohongshu", "wechat", "douyin"])
    style_override: str | None = None

    # Agent 1 output
    trend_profile: TrendProfile | None = None

    # Agent 2 output
    strategies: dict[str, PlatformStrategy] = Field(default_factory=dict)

    # Agent 3 output
    drafts: dict[str, str] = Field(default_factory=dict)

    # Agent 4 output
    review_feedback: dict[str, str] = Field(default_factory=dict)
    review_scores: dict[str, int] = Field(default_factory=dict)

    # Agent 5 output
    final_content: dict[str, str] = Field(default_factory=dict)
    title_options: dict[str, list[str]] = Field(default_factory=dict)

    # Metrics
    metrics: PipelineMetrics = Field(default_factory=PipelineMetrics)


class ModelSource(BaseModel):
    """Configuration for a single model provider."""
    name: str
    provider: str = "openai_compatible"
    base_url: str
    api_key: str
    model_name: str
    is_active: bool = False


class ReviewConfig(BaseModel):
    """Quality review thresholds."""
    score_threshold: int = 85
    max_cycles: int = 2


class AppConfig(BaseModel):
    """Top-level application configuration."""
    model_sources: list[ModelSource] = Field(default_factory=list)
    active_source: str = ""
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    default_platforms: list[str] = Field(
        default_factory=lambda: ["xiaohongshu", "wechat", "douyin"]
    )


def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    """Load app config from YAML file."""
    path = Path(config_path)
    if not path.exists():
        return AppConfig()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return AppConfig(**data)


def save_config(config: AppConfig, config_path: str = "config/config.yaml"):
    """Save app config to YAML file."""
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(), f, allow_unicode=True, default_flow_style=False)
