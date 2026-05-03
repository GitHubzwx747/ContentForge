import json
import re
import time
from pathlib import Path

from src.model.provider import ModelProvider
from src.platforms.profiles import get_profile
from src.storage.models import AgentMetrics, PipelineState, PlatformStrategy


class StrategyPlanner:
    """Agent 2: Create per-platform content strategies from trend profile."""

    def __init__(self, provider: ModelProvider, prompt_dir: str = "config/prompts"):
        self.provider = provider
        self.prompt_template = (Path(prompt_dir) / "strategy_planner.md").read_text(encoding="utf-8")

    async def run(self, state: PipelineState) -> PipelineState:
        profile_lines = []
        for p in state.platforms:
            prof = get_profile(p)
            profile_lines.append(f"- {prof.display_name}: 调性={prof.tone}, 关键词={prof.style_keywords}")
        platform_profiles_text = "\n".join(profile_lines)

        trend_profile_text = state.trend_profile.model_dump_json(indent=2) if state.trend_profile else ""

        prompt = self.prompt_template\
            .replace("{trend_profile}", trend_profile_text)\
            .replace("{platforms}", ", ".join(state.platforms))\
            .replace("{platform_profiles}", platform_profiles_text)

        messages = [{"role": "user", "content": prompt}]
        start = time.time()
        result = await self.provider.chat(messages)
        duration = time.time() - start

        content = result.content.strip()
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
        json_str = json_match.group(1).strip() if json_match else content
        data = json.loads(json_str)

        strategies = {}
        for platform, strategy_data in data.items():
            strategies[platform] = PlatformStrategy(**strategy_data)
        state.strategies = strategies

        state.metrics.agents.append(AgentMetrics(
            agent_name="strategy_planner",
            duration_seconds=round(duration, 2),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
        ))
        return state
