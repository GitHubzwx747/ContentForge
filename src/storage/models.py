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
