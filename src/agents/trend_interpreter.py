import json
import re
import time
from pathlib import Path

from src.model.provider import ModelProvider
from src.storage.models import AgentMetrics, PipelineState, TrendProfile


class TrendInterpreter:
    """Agent 1: Parse trending topic markdown into structured trend profile."""

    def __init__(self, provider: ModelProvider, prompt_dir: str = "config/prompts"):
        self.provider = provider
        self.prompt_template = (Path(prompt_dir) / "trend_interpreter.md").read_text(encoding="utf-8")

    async def run(self, state: PipelineState) -> PipelineState:
        prompt = self.prompt_template.replace("{trend_markdown}", state.trend_markdown)
        messages = [{"role": "user", "content": prompt}]

        start = time.time()
        result = await self.provider.chat(messages)
        duration = time.time() - start

        # Parse JSON, handling markdown fences
        content = result.content.strip()
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
        json_str = json_match.group(1).strip() if json_match else content
        data = json.loads(json_str)

        state.trend_profile = TrendProfile(**data)
        state.metrics.agents.append(AgentMetrics(
            agent_name="trend_interpreter",
            duration_seconds=round(duration, 2),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
        ))
        return state
