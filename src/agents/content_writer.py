import time
from pathlib import Path

from src.model.provider import ModelProvider
from src.platforms.profiles import get_profile
from src.storage.models import AgentMetrics, PipelineState


class ContentWriter:
    """Agent 3: Generate platform-adapted content drafts."""

    def __init__(self, provider: ModelProvider, prompt_dir: str = "config/prompts"):
        self.provider = provider
        self.prompt_template = (Path(prompt_dir) / "content_writer.md").read_text(encoding="utf-8")

    async def run(self, state: PipelineState) -> PipelineState:
        drafts = {}
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        total_duration = 0.0

        for platform in state.platforms:
            strategy = state.strategies.get(platform)
            if not strategy:
                continue

            profile = get_profile(platform)
            review_feedback = state.review_feedback.get(platform, "无（首次创作）")
            style_override = state.style_override or "无"

            prompt = self.prompt_template\
                .replace("{strategy}", strategy.model_dump_json(indent=2))\
                .replace("{platform_profile}", f"{profile.display_name}: {profile.tone}")\
                .replace("{style_override}", style_override)\
                .replace("{review_feedback}", review_feedback)

            messages = [{"role": "user", "content": prompt}]
            start = time.time()
            result = await self.provider.chat(messages)
            duration = time.time() - start

            drafts[platform] = result.content
            total_input_tokens += result.input_tokens
            total_output_tokens += result.output_tokens
            total_tokens += result.total_tokens
            total_duration += duration

        state.drafts = drafts
        state.metrics.agents.append(AgentMetrics(
            agent_name="content_writer",
            duration_seconds=round(total_duration, 2),
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_tokens,
        ))
        return state
