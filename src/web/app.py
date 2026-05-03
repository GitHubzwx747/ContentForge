import dataclasses
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.model.provider import ModelProvider
from src.orchestrator.langgraph_impl import LangGraphOrchestrator
from src.storage.database import Database
from src.storage.models import (
    AppConfig,
    ModelSource,
    PipelineState,
    load_config,
    save_config,
)
from src.platforms.profiles import PROFILES

CONFIG_PATH = "config/config.yaml"

db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    yield
    await db.close()


app = FastAPI(title="ContentForge", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request models ---

class GenerateRequest(BaseModel):
    text: str
    platforms: list[str] = ["xiaohongshu", "wechat", "douyin"]


class SwitchModelRequest(BaseModel):
    name: str


class AddModelRequest(BaseModel):
    name: str
    base_url: str
    api_key: str
    model_name: str
    provider: str = "openai_compatible"


# --- Helpers ---

def _get_config() -> AppConfig:
    return load_config(CONFIG_PATH)


def _get_active_provider(config: AppConfig) -> ModelProvider:
    source = next((s for s in config.model_sources if s.is_active), None)
    if not source:
        raise HTTPException(status_code=400, detail="No active model source configured")
    return ModelProvider(source)


# --- API endpoints ---

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    config = _get_config()
    provider = _get_active_provider(config)
    orch = LangGraphOrchestrator(
        provider,
        prompt_dir="config/prompts",
        score_threshold=config.review.score_threshold,
        max_cycles=config.review.max_cycles,
    )

    state = PipelineState(trend_markdown=req.text, platforms=req.platforms)
    result = await orch.invoke(state)

    # Save to DB
    gen_id = await db.save_generation(
        trend_markdown=result.trend_markdown,
        platforms=req.platforms,
        final_content=result.final_content,
        review_scores=result.review_scores,
        total_tokens=result.metrics.total_tokens,
        total_duration=result.metrics.total_duration,
        review_cycles=result.metrics.review_cycles,
    )
    for m in result.metrics.agents:
        await db.save_agent_metrics(
            generation_id=gen_id,
            agent_name=m.agent_name,
            duration_seconds=m.duration_seconds,
            input_tokens=m.input_tokens,
            output_tokens=m.output_tokens,
            total_tokens=m.total_tokens,
        )

    return result.model_dump()


@app.get("/api/history")
async def get_history(limit: int = 10):
    return await db.list_generations(limit)


@app.get("/api/history/{gen_id}")
async def get_generation(gen_id: str):
    row = await db.get_generation(gen_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    metrics = await db.get_agent_metrics(gen_id)
    row["agent_metrics"] = metrics
    return row


@app.get("/api/stats")
async def get_stats():
    return await db.get_stats()


@app.get("/api/models")
async def get_models():
    config = _get_config()
    return [s.model_dump() for s in config.model_sources]


@app.post("/api/models/switch")
async def switch_model(req: SwitchModelRequest):
    config = _get_config()
    found = False
    for s in config.model_sources:
        if s.name == req.name:
            s.is_active = True
            found = True
        else:
            s.is_active = False
    if not found:
        raise HTTPException(status_code=404, detail=f"Model source not found: {req.name}")
    config.active_source = req.name
    save_config(config, CONFIG_PATH)
    return {"message": f"Switched to {req.name}"}


@app.post("/api/models")
async def add_model(req: AddModelRequest):
    config = _get_config()
    if any(s.name == req.name for s in config.model_sources):
        raise HTTPException(status_code=400, detail=f"Model source already exists: {req.name}")
    config.model_sources.append(ModelSource(
        name=req.name,
        provider=req.provider,
        base_url=req.base_url,
        api_key=req.api_key,
        model_name=req.model_name,
    ))
    save_config(config, CONFIG_PATH)
    return {"message": f"Added model source: {req.name}"}


@app.delete("/api/models/{name}")
async def delete_model(name: str):
    config = _get_config()
    original_len = len(config.model_sources)
    config.model_sources = [s for s in config.model_sources if s.name != name]
    if len(config.model_sources) == original_len:
        raise HTTPException(status_code=404, detail=f"Model source not found: {name}")
    save_config(config, CONFIG_PATH)
    return {"message": f"Removed model source: {name}"}


@app.get("/api/platforms")
async def get_platforms():
    return [dataclasses.asdict(p) for p in PROFILES.values()]


@app.get("/api/config")
async def get_config_endpoint():
    return _get_config().model_dump()


# Mount static files LAST so API routes take priority
# Serve React build output from frontend/dist/
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
