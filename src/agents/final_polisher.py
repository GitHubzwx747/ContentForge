import json
import re
import time
from pathlib import Path

from src.model.provider import ModelProvider
from src.platforms.profiles import get_profile
from src.storage.models import AgentMetrics, PipelineState


class FinalPolisher:
    """Agent 5: Polish drafts based on review feedback, produce final content."""

    def __init__(self, provider: ModelProvider, prompt_dir: str = "config/prompts"):
        self.provider = provider
        self.prompt_template = (Path(prompt_dir) / "final_polisher.md").read_text(encoding="utf-8")

    async def run(self, state: PipelineState) -> PipelineState:
        final_content = {}
        title_options = {}
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        total_duration = 0.0

        for platform in state.platforms:
            draft = state.drafts.get(platform, "")
            feedback = state.review_feedback.get(platform, "无")
            profile = get_profile(platform)

            prompt = self.prompt_template\
                .replace("{draft}", draft)\
                .replace("{review_feedback}", feedback)\
                .replace("{platform}", profile.display_name)

            messages = [{"role": "user", "content": prompt}]
            start = time.time()
            result = await self.provider.chat(messages)
            duration = time.time() - start

            content = result.content.strip()
            json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            json_str = json_match.group(1).strip() if json_match else content
            data = json.loads(json_str)

            final_content[platform] = data["final_content"]
            title_options[platform] = data["title_options"]

            total_input_tokens += result.input_tokens
            total_output_tokens += result.output_tokens
            total_tokens += result.total_tokens
            total_duration += duration

        state.final_content = final_content
        state.title_options = title_options
        state.metrics.agents.append(AgentMetrics(
            agent_name="final_polisher",
            duration_seconds=round(total_duration, 2),
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_tokens,
        ))
        return state
