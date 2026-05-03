# ContentForge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-agent pipeline that transforms trending topic markdown into platform-adapted content for Xiaohongshu, WeChat, and Douyin.

**Architecture:** 5 pure-function agents orchestrated via LangGraph through an abstract `PipelineOrchestrator` interface. Agents communicate through a shared `PipelineState` Pydantic model. A unified `ModelProvider` wraps OpenAI-compatible APIs.

**Tech Stack:** Python 3.12, LangGraph, Pydantic v2, Typer, SQLite+aiosqlite, OpenAI SDK, PyYAML

---

## File Structure

```
content-forge/
├── pyproject.toml
├── config/
│   ├── config.yaml
│   └── prompts/
│       ├── trend_interpreter.md
│       ├── strategy_planner.md
│       ├── content_writer.md
│       ├── quality_reviewer.md
│       └── final_polisher.md
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── trend_interpreter.py
│   │   ├── strategy_planner.py
│   │   ├── content_writer.py
│   │   ├── quality_reviewer.py
│   │   └── final_polisher.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── langgraph_impl.py
│   ├── model/
│   │   ├── __init__.py
│   │   └── provider.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── models.py
│   ├── platforms/
│   │   ├── __init__.py
│   │   └── profiles.py
│   └── cli/
│       ├── __init__.py
│       └── main.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_storage.py
    ├── test_provider.py
    ├── test_agents.py
    ├── test_orchestrator.py
    └── test_cli.py
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`, `src/agents/__init__.py`, `src/orchestrator/__init__.py`, `src/model/__init__.py`, `src/storage/__init__.py`, `src/platforms/__init__.py`, `src/cli/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "content-forge"
version = "0.1.0"
description = "Multi-agent content generation pipeline"
requires-python = ">=3.12"
dependencies = [
    "langgraph>=0.2.0",
    "pydantic>=2.0",
    "typer>=0.12.0",
    "openai>=1.0.0",
    "pyyaml>=6.0",
    "aiosqlite>=0.20.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create directory structure and __init__.py files**

```bash
mkdir -p content-forge/src/{agents,orchestrator,model,storage,platforms,cli}
mkdir -p content-forge/tests
mkdir -p content-forge/config/prompts
touch content-forge/src/__init__.py
touch content-forge/src/agents/__init__.py
touch content-forge/src/orchestrator/__init__.py
touch content-forge/src/model/__init__.py
touch content-forge/src/storage/__init__.py
touch content-forge/src/platforms/__init__.py
touch content-forge/src/cli/__init__.py
touch content-forge/tests/__init__.py
```

- [ ] **Step 3: Install dependencies**

```bash
cd content-forge && pip install -e ".[dev]"
```

- [ ] **Step 4: Commit**

```bash
git init && git add -A && git commit -m "chore: project scaffolding with dependencies"
```

---

## Task 2: State Models

**Files:**
- Create: `src/storage/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write tests for state models**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd content-forge && pytest tests/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.storage.models'`

- [ ] **Step 3: Implement state models**

```python
# src/storage/models.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_models.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/storage/models.py tests/test_models.py
git commit -m "feat: add Pydantic state models for pipeline"
```

---

## Task 3: Storage Layer

**Files:**
- Create: `src/storage/database.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write tests for database operations**

```python
# tests/test_storage.py
import json
import pytest
from src.storage.database import Database


@pytest.fixture
async def db(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    await db.init()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_save_and_get_generation(db):
    gen_id = await db.save_generation(
        trend_markdown="# 热点\n内容",
        platforms=["xiaohongshu", "wechat"],
        final_content={"xiaohongshu": "小红书文案", "wechat": "微信文案"},
        review_scores={"xiaohongshu": 92, "wechat": 88},
        total_tokens=28000,
        total_duration=11.9,
        review_cycles=0,
    )
    assert gen_id is not None

    record = await db.get_generation(gen_id)
    assert record is not None
    assert record["trend_markdown"] == "# 热点\n内容"
    assert json.loads(record["platforms"]) == ["xiaohongshu", "wechat"]
    assert json.loads(record["review_scores"]) == {"xiaohongshu": 92, "wechat": 88}


@pytest.mark.asyncio
async def test_save_agent_metrics(db):
    gen_id = await db.save_generation(
        trend_markdown="test",
        platforms=["xiaohongshu"],
        final_content={},
        review_scores={},
        total_tokens=100,
        total_duration=1.0,
        review_cycles=0,
    )
    await db.save_agent_metrics(
        generation_id=gen_id,
        agent_name="trend_interpreter",
        duration_seconds=1.2,
        input_tokens=500,
        output_tokens=300,
        total_tokens=800,
    )
    metrics = await db.get_agent_metrics(gen_id)
    assert len(metrics) == 1
    assert metrics[0]["agent_name"] == "trend_interpreter"


@pytest.mark.asyncio
async def test_list_generations(db):
    for i in range(3):
        await db.save_generation(
            trend_markmd=f"test {i}",
            platforms=["xiaohongshu"],
            final_content={},
            review_scores={},
            total_tokens=100,
            total_duration=1.0,
            review_cycles=0,
        )
    rows = await db.list_generations(limit=10)
    assert len(rows) == 3


@pytest.mark.asyncio
async def test_get_stats(db):
    for i in range(5):
        await db.save_generation(
            trend_markdown=f"test {i}",
            platforms=["xiaohongshu", "wechat"],
            final_content={"xiaohongshu": "a", "wechat": "b"},
            review_scores={"xiaohongshu": 90, "wechat": 85},
            total_tokens=1000,
            total_duration=10.0,
            review_cycles=0,
        )
    stats = await db.get_stats()
    assert stats["total_generations"] == 5
    assert stats["total_tokens"] == 5000
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd content-forge && pytest tests/test_storage.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement database layer**

```python
# src/storage/database.py
import json
import uuid
from datetime import datetime, timezone

import aiosqlite


class Database:
    def __init__(self, db_path: str = "content_forge.db"):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init(self):
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._create_tables()

    async def close(self):
        if self._db:
            await self._db.close()

    async def _create_tables(self):
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS generation_history (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP,
                trend_markdown TEXT,
                platforms TEXT,
                final_content TEXT,
                review_scores TEXT,
                total_tokens INTEGER,
                total_duration REAL,
                review_cycles INTEGER
            );

            CREATE TABLE IF NOT EXISTS agent_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id TEXT REFERENCES generation_history(id),
                agent_name TEXT,
                duration_seconds REAL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER
            );

            CREATE TABLE IF NOT EXISTS style_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                platform TEXT,
                prompt_template TEXT,
                created_at TIMESTAMP
            );
        """)
        await self._db.commit()

    async def save_generation(
        self,
        trend_markdown: str,
        platforms: list[str],
        final_content: dict,
        review_scores: dict,
        total_tokens: int,
        total_duration: float,
        review_cycles: int,
    ) -> str:
        gen_id = str(uuid.uuid4())
        await self._db.execute(
            """INSERT INTO generation_history
               (id, created_at, trend_markdown, platforms, final_content,
                review_scores, total_tokens, total_duration, review_cycles)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                gen_id,
                datetime.now(timezone.utc).isoformat(),
                trend_markdown,
                json.dumps(platforms, ensure_ascii=False),
                json.dumps(final_content, ensure_ascii=False),
                json.dumps(review_scores, ensure_ascii=False),
                total_tokens,
                total_duration,
                review_cycles,
            ),
        )
        await self._db.commit()
        return gen_id

    async def get_generation(self, gen_id: str) -> dict | None:
        cursor = await self._db.execute(
            "SELECT * FROM generation_history WHERE id = ?", (gen_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        columns = [d[0] for d in cursor.description]
        return dict(zip(columns, row))

    async def list_generations(self, limit: int = 10) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT * FROM generation_history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def save_agent_metrics(
        self,
        generation_id: str,
        agent_name: str,
        duration_seconds: float,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
    ):
        await self._db.execute(
            """INSERT INTO agent_metrics
               (generation_id, agent_name, duration_seconds,
                input_tokens, output_tokens, total_tokens)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (generation_id, agent_name, duration_seconds,
             input_tokens, output_tokens, total_tokens),
        )
        await self._db.commit()

    async def get_agent_metrics(self, gen_id: str) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT * FROM agent_metrics WHERE generation_id = ?", (gen_id,)
        )
        rows = await cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def get_stats(self) -> dict:
        cursor = await self._db.execute(
            """SELECT COUNT(*) as total_generations,
                      COALESCE(SUM(total_tokens), 0) as total_tokens,
                      COALESCE(AVG(total_duration), 0) as avg_duration,
                      COALESCE(AVG(total_tokens), 0) as avg_tokens
               FROM generation_history"""
        )
        row = await cursor.fetchone()
        columns = [d[0] for d in cursor.description]
        return dict(zip(columns, row))
```

- [ ] **Step 4: Fix the typo in test (`trend_markmd` → `trend_markdown`)**

```python
# In test_list_generations, fix:
trend_markdown=f"test {i}",
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_storage.py -v
```

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/storage/database.py tests/test_storage.py
git commit -m "feat: add SQLite storage layer with aiosqlite"
```

---

## Task 4: Config System

**Files:**
- Create: `config/config.yaml`
- Modify: `src/storage/models.py` (add ModelSource)

- [ ] **Step 1: Create default config.yaml**

```yaml
# config/config.yaml
model_sources:
  - name: "百炼千问"
    provider: "openai_compatible"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key: "sk-xxx"
    model_name: "qwen-plus"
    is_active: true

  - name: "DeepSeek"
    provider: "openai_compatible"
    base_url: "https://api.deepseek.com/v1"
    api_key: "sk-yyy"
    model_name: "deepseek-chat"
    is_active: false

active_source: "百炼千问"

review:
  score_threshold: 85
  max_cycles: 2

default_platforms:
  - xiaohongshu
  - wechat
  - douyin
```

- [ ] **Step 2: Add ModelSource and Config models to models.py**

Append to `src/storage/models.py`:

```python
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
```

- [ ] **Step 3: Add config loading function**

Append to `src/storage/models.py`:

```python
import yaml
from pathlib import Path


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
```

- [ ] **Step 4: Commit**

```bash
git add config/config.yaml src/storage/models.py
git commit -m "feat: add YAML config system with ModelSource"
```

---

## Task 5: Model Provider

**Files:**
- Create: `src/model/provider.py`
- Create: `tests/test_provider.py`

- [ ] **Step 1: Write tests for ModelProvider**

```python
# tests/test_provider.py
from unittest.mock import AsyncMock, MagicMock
import pytest
from src.model.provider import ModelProvider
from src.storage.models import ModelSource


def make_provider():
    source = ModelSource(
        name="test",
        base_url="http://localhost",
        api_key="sk-test",
        model_name="test-model",
    )
    return ModelProvider(source)


@pytest.mark.asyncio
async def test_chat_returns_content():
    provider = make_provider()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Hello world"))]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await provider.chat([{"role": "user", "content": "hi"}])
    assert result.content == "Hello world"
    assert result.input_tokens == 10
    assert result.output_tokens == 5


@pytest.mark.asyncio
async def test_chat_passes_model_and_messages():
    provider = make_provider()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_response.usage = MagicMock(prompt_tokens=5, completion_tokens=2, total_tokens=7)
    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    messages = [{"role": "system", "content": "you are helpful"}, {"role": "user", "content": "test"}]
    await provider.chat(messages)

    provider.client.chat.completions.create.assert_called_once()
    call_kwargs = provider.client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "test-model"
    assert call_kwargs.kwargs["messages"] == messages
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd content-forge && pytest tests/test_provider.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement ModelProvider**

```python
# src/model/provider.py
from dataclasses import dataclass

from openai import AsyncOpenAI

from src.storage.models import ModelSource


@dataclass
class ChatResult:
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


class ModelProvider:
    """Unified model call layer wrapping OpenAI-compatible APIs."""

    def __init__(self, source: ModelSource):
        self.source = source
        self.client = AsyncOpenAI(
            base_url=source.base_url,
            api_key=source.api_key,
        )

    async def chat(self, messages: list[dict], **kwargs) -> ChatResult:
        response = await self.client.chat.completions.create(
            model=self.source.model_name,
            messages=messages,
            **kwargs,
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        return ChatResult(
            content=content,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_provider.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/model/provider.py tests/test_provider.py
git commit -m "feat: add ModelProvider with OpenAI-compatible chat"
```

---

## Task 6: Platform Profiles

**Files:**
- Create: `src/platforms/profiles.py`

- [ ] **Step 1: Implement platform profiles**

```python
# src/platforms/profiles.py
from dataclasses import dataclass, field


@dataclass
class PlatformProfile:
    """Platform-specific content characteristics."""
    name: str
    display_name: str
    max_length: int
    style_keywords: list[str] = field(default_factory=list)
    structure_hints: list[str] = field(default_factory=list)
    tone: str = ""


PROFILES: dict[str, PlatformProfile] = {
    "xiaohongshu": PlatformProfile(
        name="xiaohongshu",
        display_name="小红书",
        max_length=1000,
        style_keywords=["种草", "分享", "安利", "绝绝子", "姐妹们"],
        structure_hints=["emoji节奏", "分段标题", "图文搭配提示"],
        tone="轻松活泼、闺蜜感",
    ),
    "wechat": PlatformProfile(
        name="wechat",
        display_name="微信公众号",
        max_length=5000,
        style_keywords=["深度", "洞察", "思考", "分析"],
        structure_hints=["深度观点", "结构化论证", "金句收尾"],
        tone="专业深度、有观点",
    ),
    "douyin": PlatformProfile(
        name="douyin",
        display_name="抖音",
        max_length=500,
        style_keywords=["爆款", "震惊", "没想到", "家人们"],
        structure_hints=["前3秒hook", "口语化", "节奏感强"],
        tone="口语化、节奏快、有冲击力",
    ),
}


def get_profile(platform: str) -> PlatformProfile:
    """Get platform profile by name."""
    if platform not in PROFILES:
        raise ValueError(f"Unknown platform: {platform}. Available: {list(PROFILES.keys())}")
    return PROFILES[platform]


def list_platforms() -> list[str]:
    """Return all available platform names."""
    return list(PROFILES.keys())
```

- [ ] **Step 2: Commit**

```bash
git add src/platforms/profiles.py
git commit -m "feat: add platform profiles for xiaohongshu/wechat/douyin"
```

---

## Task 7: Prompt Templates

**Files:**
- Create: `config/prompts/trend_interpreter.md`
- Create: `config/prompts/strategy_planner.md`
- Create: `config/prompts/content_writer.md`
- Create: `config/prompts/quality_reviewer.md`
- Create: `config/prompts/final_polisher.md`

- [ ] **Step 1: Create trend_interpreter.md**

```markdown
# 热点解读 Agent

你是一位资深舆情分析师。请分析以下热点内容，输出结构化的热点画像。

## 输入内容
{trend_markdown}

## 输出要求（严格JSON格式）
```json
{{
  "core_event": "一句话概括核心事件",
  "key_data": ["关键数据点1", "关键数据点2"],
  "sentiment": "正面/争议/焦虑/期待（四选一）",
  "angles": ["切入角度1", "切入角度2", "切入角度3"]
}}
```

## 分析维度
1. 事件本质：发生了什么？为什么重要？
2. 关键数据：有哪些数字、比例、时间节点？
3. 情绪倾向：公众情绪是正面、争议、焦虑还是期待？
4. 内容角度：至少3个可切入的创作角度
```

- [ ] **Step 2: Create strategy_planner.md**

```markdown
# 策略规划 Agent

你是一位跨平台内容策略专家。请基于热点画像，为目标平台制定内容策略。

## 热点画像
{trend_profile}

## 目标平台
{platforms}

## 平台特性参考
{platform_profiles}

## 输出要求（严格JSON格式）
```json
{{
  "platform_name": {{
    "angle": "选题角度",
    "audience": "目标受众描述",
    "structure": {{
      "hook": "开头策略",
      "body": "主体结构",
      "cta": "结尾引导"
    }},
    "emotion_hook": "情绪共鸣点"
  }}
}}
```

请为每个目标平台输出一个策略卡。
```

- [ ] **Step 3: Create content_writer.md**

```markdown
# 文案创作 Agent

你是一位精通多平台风格的爆款文案写手。请根据策略卡创作文案。

## 策略卡
{strategy}

## 平台特性
{platform_profile}

## 风格覆盖（如有）
{style_override}

## 创作要求
- 严格遵循平台调性和结构要求
- 内容要有信息增量，不要空洞
- 标题要有吸引力
- 如有评审意见，请根据意见修改

## 评审意见（如有）
{review_feedback}

## 输出
直接输出完整文案，包含标题和正文。不要输出JSON。
```

- [ ] **Step 4: Create quality_reviewer.md**

```markdown
# 质量评审 Agent

你是一位严格的内容质量审核官。请评审以下文案。

## 平台
{platform}

## 平台调性要求
{platform_profile}

## 待审文案
{draft}

## 评审维度（每项0-100分）
1. **平台调性一致性** - 是否符合平台风格？
2. **标题吸引力** - 标题是否能吸引点击？
3. **信息准确性** - 内容是否有事实错误？
4. **敏感词/违规** - 是否有平台违规风险？
5. **整体质量** - 综合评分

## 输出要求（严格JSON格式）
```json
{{
  "score": 90,
  "feedback": "详细评审意见，包含具体修改建议"
}}
```
```

- [ ] **Step 5: Create final_polisher.md**

```markdown
# 终稿打磨 Agent

你是一位文案终审编辑。请根据评审意见打磨文案，输出最终定稿。

## 原始文案
{draft}

## 评审意见
{review_feedback}

## 平台
{platform}

## 打磨要求
1. 根据评审意见修正问题
2. 添加话题标签和热门关键词
3. 生成3个备选标题

## 输出要求（严格JSON格式）
```json
{{
  "final_content": "最终文案内容（含标题和正文）",
  "title_options": ["标题选项1", "标题选项2", "标题选项3"]
}}
```
```

- [ ] **Step 6: Commit**

```bash
git add config/prompts/
git commit -m "feat: add prompt templates for all 5 agents"
```

---

## Task 8: Agent 1 — TrendInterpreter

**Files:**
- Create: `src/agents/trend_interpreter.py`
- Modify: `tests/test_agents.py` (create, add trend interpreter tests)

- [ ] **Step 1: Write failing test**

```python
# tests/test_agents.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd content-forge && pytest tests/test_agents.py::test_trend_interpreter_parses_json -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement TrendInterpreter**

```python
# src/agents/trend_interpreter.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_agents.py -v -k "trend"
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/agents/trend_interpreter.py tests/test_agents.py
git commit -m "feat: add TrendInterpreter agent with JSON parsing"
```

---

## Task 9: Agent 2 — StrategyPlanner

**Files:**
- Modify: `src/agents/strategy_planner.py`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_agents.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd content-forge && pytest tests/test_agents.py::test_strategy_planner_creates_strategies -v
```

Expected: FAIL

- [ ] **Step 3: Implement StrategyPlanner**

```python
# src/agents/strategy_planner.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_agents.py -v -k "strategy"
```

Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/agents/strategy_planner.py tests/test_agents.py
git commit -m "feat: add StrategyPlanner agent"
```

---

## Task 10: Agent 3 — ContentWriter

**Files:**
- Create: `src/agents/content_writer.py`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_agents.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd content-forge && pytest tests/test_agents.py::test_content_writer_creates_drafts -v
```

Expected: FAIL

- [ ] **Step 3: Implement ContentWriter**

```python
# src/agents/content_writer.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_agents.py -v -k "content_writer"
```

Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/agents/content_writer.py tests/test_agents.py
git commit -m "feat: add ContentWriter agent"
```

---

## Task 11: Agent 4 — QualityReviewer

**Files:**
- Create: `src/agents/quality_reviewer.py`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_agents.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd content-forge && pytest tests/test_agents.py::test_quality_reviewer_scores_drafts -v
```

Expected: FAIL

- [ ] **Step 3: Implement QualityReviewer**

```python
# src/agents/quality_reviewer.py
import json
import re
import time
from pathlib import Path

from src.model.provider import ModelProvider
from src.platforms.profiles import get_profile
from src.storage.models import AgentMetrics, PipelineState


class QualityReviewer:
    """Agent 4: Review content quality and assign scores."""

    def __init__(self, provider: ModelProvider, prompt_dir: str = "config/prompts"):
        self.provider = provider
        self.prompt_template = (Path(prompt_dir) / "quality_reviewer.md").read_text(encoding="utf-8")

    async def run(self, state: PipelineState) -> PipelineState:
        review_feedback = {}
        review_scores = {}
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        total_duration = 0.0

        for platform in state.platforms:
            draft = state.drafts.get(platform, "")
            profile = get_profile(platform)

            prompt = self.prompt_template\
                .replace("{platform}", profile.display_name)\
                .replace("{platform_profile}", f"{profile.display_name}: {profile.tone}")\
                .replace("{draft}", draft)

            messages = [{"role": "user", "content": prompt}]
            start = time.time()
            result = await self.provider.chat(messages)
            duration = time.time() - start

            content = result.content.strip()
            json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            json_str = json_match.group(1).strip() if json_match else content
            data = json.loads(json_str)

            review_scores[platform] = data["score"]
            review_feedback[platform] = data["feedback"]

            total_input_tokens += result.input_tokens
            total_output_tokens += result.output_tokens
            total_tokens += result.total_tokens
            total_duration += duration

        state.review_feedback = review_feedback
        state.review_scores = review_scores
        state.metrics.agents.append(AgentMetrics(
            agent_name="quality_reviewer",
            duration_seconds=round(total_duration, 2),
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_tokens,
        ))
        return state
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_agents.py -v -k "quality_reviewer"
```

Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/agents/quality_reviewer.py tests/test_agents.py
git commit -m "feat: add QualityReviewer agent"
```

---

## Task 12: Agent 5 — FinalPolisher

**Files:**
- Create: `src/agents/final_polisher.py`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_agents.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd content-forge && pytest tests/test_agents.py::test_final_polisher_produces_final_content -v
```

Expected: FAIL

- [ ] **Step 3: Implement FinalPolisher**

```python
# src/agents/final_polisher.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_agents.py -v -k "final_polisher"
```

Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/agents/final_polisher.py tests/test_agents.py
git commit -m "feat: add FinalPolisher agent"
```

---

## Task 13: Orchestrator (LangGraph Pipeline)

**Files:**
- Create: `src/orchestrator/base.py`
- Create: `src/orchestrator/langgraph_impl.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write tests for orchestrator**

```python
# tests/test_orchestrator.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.orchestrator.langgraph_impl import LangGraphOrchestrator
from src.model.provider import ChatResult
from src.storage.models import PipelineState


def make_mock_provider():
    """Create a mock provider that returns valid JSON for each agent."""
    call_count = 0

    responses = [
        # Agent 1: TrendInterpreter
        json.dumps({"core_event": "AI爆发", "key_data": ["GPT-5"], "sentiment": "期待", "angles": ["技术"]}, ensure_ascii=False),
        # Agent 2: StrategyPlanner
        json.dumps({"xiaohongshu": {"angle": "效率", "audience": "白领", "structure": {"hook": "h", "body": "b", "cta": "c"}, "emotion_hook": "e"}}, ensure_ascii=False),
        # Agent 3: ContentWriter
        "# 小红书文案\n\n正文内容",
        # Agent 4: QualityReviewer
        json.dumps({"score": 90, "feedback": "不错"}, ensure_ascii=False),
        # Agent 5: FinalPolisher
        json.dumps({"final_content": "# 最终文案\n\n定稿", "title_options": ["标题1", "标题2", "标题3"]}, ensure_ascii=False),
    ]

    async def mock_chat(messages, **kwargs):
        nonlocal call_count
        content = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return ChatResult(content=content, input_tokens=100, output_tokens=50, total_tokens=150)

    provider = MagicMock()
    provider.chat = AsyncMock(side_effect=mock_chat)
    return provider


@pytest.mark.asyncio
async def test_orchestrator_runs_full_pipeline():
    provider = make_mock_provider()
    orch = LangGraphOrchestrator(provider, prompt_dir="config/prompts", score_threshold=85, max_cycles=2)

    state = PipelineState(
        trend_markdown="# AI Agent爆发\n内容...",
        platforms=["xiaohongshu"],
    )
    result = await orch.invoke(state)

    assert result.trend_profile is not None
    assert "xiaohongshu" in result.strategies
    assert "xiaohongshu" in result.drafts
    assert "xiaohongshu" in result.review_scores
    assert "xiaohongshu" in result.final_content
    assert len(result.title_options["xiaohongshu"]) == 3
    assert len(result.metrics.agents) == 5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd content-forge && pytest tests/test_orchestrator.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement abstract base**

```python
# src/orchestrator/base.py
from abc import ABC, abstractmethod

from src.storage.models import PipelineState


class PipelineOrchestrator(ABC):
    """Abstract interface for pipeline orchestration. Implementations are swappable."""

    @abstractmethod
    async def invoke(self, state: PipelineState) -> PipelineState:
        """Execute the full agent pipeline and return final state."""
        ...
```

- [ ] **Step 4: Implement LangGraph orchestrator**

```python
# src/orchestrator/langgraph_impl.py
import time

from langgraph.graph import StateGraph, END

from src.agents.content_writer import ContentWriter
from src.agents.final_polisher import FinalPolisher
from src.agents.quality_reviewer import QualityReviewer
from src.agents.strategy_planner import StrategyPlanner
from src.agents.trend_interpreter import TrendInterpreter
from src.model.provider import ModelProvider
from src.orchestrator.base import PipelineOrchestrator
from src.storage.models import PipelineMetrics, PipelineState


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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd content-forge && pytest tests/test_orchestrator.py -v
```

Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add src/orchestrator/base.py src/orchestrator/langgraph_impl.py tests/test_orchestrator.py
git commit -m "feat: add LangGraph orchestrator with review loop"
```

---

## Task 14: CLI

**Files:**
- Create: `src/cli/main.py`

- [ ] **Step 1: Implement CLI with generate command**

```python
# src/cli/main.py
import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.model.provider import ModelProvider
from src.orchestrator.langgraph_impl import LangGraphOrchestrator
from src.storage.database import Database
from src.storage.models import AppConfig, ModelSource, PipelineState, load_config, save_config

app = typer.Typer(help="ContentForge - Multi-agent content generation")
console = Console()

CONFIG_PATH = "config/config.yaml"


def get_config() -> AppConfig:
    return load_config(CONFIG_PATH)


def get_active_provider(config: AppConfig) -> ModelProvider:
    source = next((s for s in config.model_sources if s.is_active), None)
    if not source:
        console.print("[red]No active model source. Use 'model use' to select one.[/red]")
        raise typer.Exit(1)
    return ModelProvider(source)


@app.command()
def generate(
    input: str = typer.Argument(..., help="Path to trend markdown file"),
    platforms: str = typer.Option("xiaohongshu,wechat,douyin", help="Comma-separated platform list"),
):
    """Generate content from trend markdown."""
    input_path = Path(input)
    if not input_path.exists():
        console.print(f"[red]File not found: {input}[/red]")
        raise typer.Exit(1)

    trend_markdown = input_path.read_text(encoding="utf-8")
    platform_list = [p.strip() for p in platforms.split(",")]

    config = get_config()
    provider = get_active_provider(config)
    orch = LangGraphOrchestrator(
        provider,
        prompt_dir="config/prompts",
        score_threshold=config.review.score_threshold,
        max_cycles=config.review.max_cycles,
    )

    state = PipelineState(trend_markdown=trend_markdown, platforms=platform_list)

    console.print("\n[bold]正在执行流水线...[/bold]\n")

    result = asyncio.run(orch.invoke(state))

    # Print agent progress
    for i, m in enumerate(result.metrics.agents):
        console.print(f"━━━ Agent {i+1}/{len(result.metrics.agents)}: {m.agent_name} ━━━")
        console.print(f"  ✓ 完成 ({m.duration_seconds}s) | tokens: {m.input_tokens} → {m.output_tokens} | 总计: {m.total_tokens}")

    # Print summary
    console.print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    console.print("✓ 流水线完成\n")
    console.print(f"  总耗时: {result.metrics.total_duration}s")
    console.print(f"  总Token: {result.metrics.total_tokens}")
    console.print(f"  平均评分: {result.metrics.average_score}")
    console.print(f"  质检循环: {result.metrics.review_cycles - 1}次")

    # Print content
    for platform in platform_list:
        profile_name = {"xiaohongshu": "小红书", "wechat": "微信公众号", "douyin": "抖音"}.get(platform, platform)
        console.print(f"\n--- {profile_name} ---")
        if platform in result.final_content:
            console.print(result.final_content[platform])
        if platform in result.title_options:
            console.print(f"\n备选标题: {result.title_options[platform]}")

    # Save to DB
    asyncio.run(_save_result(result, platform_list))


async def _save_result(result: PipelineState, platforms: list[str]):
    db = Database()
    await db.init()
    gen_id = await db.save_generation(
        trend_markdown=result.trend_markdown,
        platforms=platforms,
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
    await db.close()
    console.print(f"\n[dim]已保存到数据库，ID: {gen_id}[/dim]")


# --- Model management subcommand ---
model_app = typer.Typer(help="Model source management")
app.add_typer(model_app, name="model")


@model_app.command("list")
def model_list():
    """List all configured model sources."""
    config = get_config()
    table = Table(title="模型源列表")
    table.add_column("名称")
    table.add_column("模型")
    table.add_column("Base URL")
    table.add_column("状态")
    for s in config.model_sources:
        status = "✓ 当前" if s.is_active else ""
        table.add_row(s.name, s.model_name, s.base_url, status)
    console.print(table)


@model_app.command("use")
def model_use(name: str = typer.Argument(..., help="Model source name to activate")):
    """Switch active model source."""
    config = get_config()
    found = False
    for s in config.model_sources:
        if s.name == name:
            s.is_active = True
            found = True
        else:
            s.is_active = False
    if not found:
        console.print(f"[red]Model source not found: {name}[/red]")
        raise typer.Exit(1)
    config.active_source = name
    save_config(config, CONFIG_PATH)
    console.print(f"[green]✓ 已切换到 {name}[/green]")


@model_app.command("add")
def model_add(
    name: str = typer.Option(..., help="Model source name"),
    base_url: str = typer.Option(..., help="API base URL"),
    api_key: str = typer.Option(..., help="API key"),
    model: str = typer.Option(..., help="Model name"),
):
    """Add a new model source."""
    config = get_config()
    if any(s.name == name for s in config.model_sources):
        console.print(f"[red]Model source already exists: {name}[/red]")
        raise typer.Exit(1)
    config.model_sources.append(ModelSource(
        name=name, base_url=base_url, api_key=api_key, model_name=model,
    ))
    save_config(config, CONFIG_PATH)
    console.print(f"[green]✓ 已添加模型源: {name}[/green]")


@model_app.command("remove")
def model_remove(name: str = typer.Argument(..., help="Model source name to remove")):
    """Remove a model source."""
    config = get_config()
    original_len = len(config.model_sources)
    config.model_sources = [s for s in config.model_sources if s.name != name]
    if len(config.model_sources) == original_len:
        console.print(f"[red]Model source not found: {name}[/red]")
        raise typer.Exit(1)
    save_config(config, CONFIG_PATH)
    console.print(f"[green]✓ 已删除模型源: {name}[/green]")


# --- History command ---
@app.command()
def history(limit: int = typer.Option(10, help="Number of records")):
    """View generation history."""
    async def _run():
        db = Database()
        await db.init()
        rows = await db.list_generations(limit)
        await db.close()
        return rows

    rows = asyncio.run(_run())
    table = Table(title="生成历史")
    table.add_column("ID", max_width=8)
    table.add_column("时间")
    table.add_column("平台")
    table.add_column("评分")
    table.add_column("Token")
    for row in rows:
        table.add_row(
            row["id"][:8],
            str(row["created_at"])[:19],
            row["platforms"],
            str(row["review_scores"]),
            str(row["total_tokens"]),
        )
    console.print(table)


# --- Interactive mode ---
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """ContentForge interactive mode."""
    if ctx.invoked_subcommand is not None:
        return

    console.print("[bold]ContentForge - 多智能体文案生成系统[/bold]")
    console.print("输入 /help 查看可用命令\n")

    while True:
        try:
            user_input = console.input("[bold cyan]> [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n再见!")
            break

        if not user_input:
            continue

        if user_input in ("/quit", "/exit", "/q"):
            console.print("再见!")
            break

        if user_input == "/help":
            console.print("""
可用命令:
  /generate <文件路径> [--platforms x,y,z]  生成文案
  /model list                               查看模型源
  /model use <名称>                         切换模型源
  /history                                  查看生成历史
  /help                                     显示帮助
  /clear                                    清屏
  /quit                                     退出
""")
            continue

        if user_input == "/clear":
            console.clear()
            continue

        if user_input.startswith("/generate"):
            parts = user_input.split()
            if len(parts) < 2:
                console.print("[red]用法: /generate <文件路径>[/red]")
                continue
            file_path = parts[1]
            platforms = "xiaohongshu,wechat,douyin"
            for part in parts[2:]:
                if part.startswith("--platforms="):
                    platforms = part.split("=", 1)[1]
            # Invoke generate via Typer
            try:
                generate(input=file_path, platforms=platforms)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            continue

        if user_input.startswith("/model"):
            parts = user_input.split()
            if len(parts) == 1:
                model_list()
            elif parts[1] == "list":
                model_list()
            elif parts[1] == "use" and len(parts) >= 3:
                model_use(name=parts[2])
            else:
                console.print("[red]用法: /model [list|use <名称>][/red]")
            continue

        if user_input == "/history":
            history(limit=10)
            continue

        console.print(f"[yellow]未知命令: {user_input}. 输入 /help 查看帮助.[/yellow]")


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Commit**

```bash
git add src/cli/main.py
git commit -m "feat: add Typer CLI with interactive mode and model management"
```

---

## Task 15: Integration Smoke Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test with mock provider**

```python
# tests/test_integration.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.model.provider import ChatResult
from src.orchestrator.langgraph_impl import LangGraphOrchestrator
from src.storage.models import PipelineState


def make_full_mock_provider():
    """Mock provider covering full pipeline flow."""
    responses = [
        # TrendInterpreter
        json.dumps({
            "core_event": "AI Agent技术爆发",
            "key_data": ["OpenAI发布GPT-5", "Anthropic发布Claude 4"],
            "sentiment": "期待",
            "angles": ["技术趋势", "职场影响", "创业机会"],
        }, ensure_ascii=False),
        # StrategyPlanner
        json.dumps({
            "xiaohongshu": {
                "angle": "职场效率革命",
                "audience": "25-35岁职场白领",
                "structure": {"hook": "痛点引入", "body": "案例+数据", "cta": "关注获取更多"},
                "emotion_hook": "焦虑→希望",
            },
        }, ensure_ascii=False),
        # ContentWriter
        "🔥 AI Agent到底有多强？实测后我惊了\n\n正文内容在这里...\n\n#AI #效率",
        # QualityReviewer
        json.dumps({"score": 92, "feedback": "标题吸引力强，内容结构清晰，建议增加具体数据"}, ensure_ascii=False),
        # FinalPolisher
        json.dumps({
            "final_content": "🔥 AI Agent到底有多强？实测后我惊了\n\n最终定稿内容...\n\n#AI #效率 #Agent",
            "title_options": [
                "AI Agent到底有多强？实测后我惊了",
                "用了AI Agent后，我的效率翻了3倍",
                "2026年了，你还没用AI Agent？",
            ],
        }, ensure_ascii=False),
    ]
    call_count = 0

    async def mock_chat(messages, **kwargs):
        nonlocal call_count
        content = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return ChatResult(content=content, input_tokens=200, output_tokens=100, total_tokens=300)

    provider = MagicMock()
    provider.chat = AsyncMock(side_effect=mock_chat)
    return provider


@pytest.mark.asyncio
async def test_full_pipeline_produces_complete_output():
    provider = make_full_mock_provider()
    orch = LangGraphOrchestrator(provider, prompt_dir="config/prompts", score_threshold=85, max_cycles=2)

    state = PipelineState(
        trend_markdown="# AI Agent爆发\n\nOpenAI发布GPT-5...",
        platforms=["xiaohongshu"],
    )
    result = await orch.invoke(state)

    # All pipeline stages completed
    assert result.trend_profile is not None
    assert result.trend_profile.core_event == "AI Agent技术爆发"
    assert "xiaohongshu" in result.strategies
    assert "xiaohongshu" in result.drafts
    assert "xiaohongshu" in result.review_scores
    assert result.review_scores["xiaohongshu"] == 92
    assert "xiaohongshu" in result.final_content
    assert len(result.title_options["xiaohongshu"]) == 3

    # Metrics populated
    assert result.metrics.total_tokens > 0
    assert result.metrics.total_duration > 0
    assert result.metrics.average_score == 92.0
    assert len(result.metrics.agents) == 5
```

- [ ] **Step 2: Run all tests**

```bash
cd content-forge && pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration smoke test for full pipeline"
```

---

## Self-Review Checklist

- [x] All 5 agents implemented (TrendInterpreter, StrategyPlanner, ContentWriter, QualityReviewer, FinalPolisher)
- [x] PipelineState with all fields from spec section 3.2
- [x] PipelineMetrics with all fields from spec section 3.3
- [x] Abstract orchestrator interface (base.py) for swappability
- [x] LangGraph implementation with conditional review loop (score < threshold → rewrite, max 2 cycles)
- [x] ModelProvider wrapping OpenAI-compatible API
- [x] Config system (YAML) with model source management
- [x] SQLite storage for generation history and agent metrics
- [x] Platform profiles for xiaohongshu, wechat, douyin
- [x] Prompt templates in markdown files
- [x] CLI with generate, model, history commands + interactive mode
- [x] All prompt template placeholders ({trend_markdown}, {trend_profile}, etc.) match agent code
- [x] Type names consistent across tasks (TrendProfile, PlatformStrategy, PipelineState, etc.)
- [x] No placeholders, TBDs, or "similar to Task N" patterns
