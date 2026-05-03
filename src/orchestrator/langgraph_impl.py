import time

from langgraph.graph import StateGraph, END

from src.agents.content_writer import ContentWriter
from src.agents.final_polisher import FinalPolisher
from src.agents.quality_reviewer import QualityReviewer
from src.agents.strategy_planner import StrategyPlanner
from src.agents.trend_interpreter import TrendInterpreter
from src.model.provider import ModelProvider
from src.orchestrator.base import PipelineOrchestrator
from src.storage.models import PipelineState


class LangGraphOrchestrator(PipelineOrchestrator):
    """LangGraph-based pipeline implementation with quality review loop."""

    def __init__(
        self,
        provider: ModelProvider,
        prompt_dir: str = "config/prompts",
        score_threshold: int = 85,
        max_cycles: int = 2,
    ):
        self.provider = provider
        self.prompt_dir = prompt_dir
        self.score_threshold = score_threshold
        self.max_cycles = max_cycles

        self.trend_interpreter = TrendInterpreter(provider, prompt_dir)
        self.strategy_planner = StrategyPlanner(provider, prompt_dir)
        self.content_writer = ContentWriter(provider, prompt_dir)
        self.quality_reviewer = QualityReviewer(provider, prompt_dir)
        self.final_polisher = FinalPolisher(provider, prompt_dir)

        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(PipelineState)

        graph.add_node("interpret_trend", self._run_interpret)
        graph.add_node("plan_strategy", self._run_strategy)
        graph.add_node("write_content", self._run_write)
        graph.add_node("review_quality", self._run_review)
        graph.add_node("polish_final", self._run_polish)

        graph.set_entry_point("interpret_trend")
        graph.add_edge("interpret_trend", "plan_strategy")
        graph.add_edge("plan_strategy", "write_content")
        graph.add_edge("write_content", "review_quality")
        graph.add_conditional_edges(
            "review_quality",
            self._should_rewrite,
            {"rewrite": "write_content", "polish": "polish_final"},
        )
        graph.add_edge("polish_final", END)

        return graph.compile()

    async def _run_interpret(self, state: PipelineState) -> PipelineState:
        return await self.trend_interpreter.run(state)

    async def _run_strategy(self, state: PipelineState) -> PipelineState:
        return await self.strategy_planner.run(state)

    async def _run_write(self, state: PipelineState) -> PipelineState:
        return await self.content_writer.run(state)

    async def _run_review(self, state: PipelineState) -> PipelineState:
        result = await self.quality_reviewer.run(state)
        state.metrics.review_cycles += 1
        return result

    async def _run_polish(self, state: PipelineState) -> PipelineState:
        return await self.final_polisher.run(state)

    def _should_rewrite(self, state: PipelineState) -> str:
        """Decide whether to rewrite or polish based on review scores."""
        if state.metrics.review_cycles >= self.max_cycles:
            return "polish"
        for platform, score in state.review_scores.items():
            if score < self.score_threshold:
                return "rewrite"
        return "polish"

    async def invoke(self, state: PipelineState) -> PipelineState:
        start = time.time()
        result = await self._graph.ainvoke(state)
        total_duration = time.time() - start

        # If result is a dict (from LangGraph), convert back to PipelineState
        if isinstance(result, dict):
            result = PipelineState(**result)

        result.metrics.total_duration = round(total_duration, 2)
        result.metrics.total_tokens = sum(a.total_tokens for a in result.metrics.agents)

        scores = list(result.review_scores.values())
        result.metrics.average_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        return result
