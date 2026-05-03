# ContentForge - 多智能体文案生成系统设计文档

## 1. 项目概述

### 1.1 定位

个人效率工具 + 秋招简历技术作品。基于多Agent流水线协作，将热点信息自动生成适配多平台的爆款文案。

### 1.2 核心价值

- **效率提升**: 输入热点MD → 自动输出小红书/微信/抖音三平台文案
- **技术深度**: LangGraph多Agent编排、质检循环、全链路Token追踪
- **可扩展**: 编排层抽象接口，支持从LangGraph替换为自研框架

### 1.3 边界

- **负责**: 文案生成全流程（热点解读 → 策略规划 → 文案创作 → 质量评审 → 终稿打磨）
- **不负责**: 热点采集（由外部工具 trendradar 提供）

---

## 2. 架构设计

### 2.1 整体架构

```
┌──────────────────────────────────────────────────────────┐
│                    CLI / Web UI                           │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              Pipeline Orchestrator (抽象接口)              │
│    ┌─────────────────────────────────────────────┐       │
│    │  LangGraph实现  ← 当前使用                    │       │
│    │  自研实现        ← 未来可替换                  │       │
│    └─────────────────────────────────────────────┘       │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                   Agent 层（纯业务逻辑）                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐   │
│  │ 热点解读  │→│ 策略规划  │→│ 文案创作  │→│ 质量评审│   │
│  └──────────┘  └──────────┘  └──────────┘  └───┬────┘   │
│                                                 │        │
│                                    评分低? ──→ 回流修改   │
│                                                 │        │
│                                          ┌──────▼─────┐  │
│                                          │  终稿打磨   │  │
│                                          └────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Model Provider│  │  SQLite存储   │  │  平台特性库   │
│ (可切换)      │  │ (历史/指标)   │  │ (风格模板)    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 2.2 解耦策略

核心原则：**Agent纯函数化 + 编排层抽象接口**，确保未来可替换LangGraph。

- **Orchestrator接口**: 定义 `pipeline.invoke(state)` 标准方法
- **Agent纯函数**: 每个Agent只做输入→输出转换，不依赖框架API
- **State标准化**: Pydantic定义状态模型，与框架无关

---

## 3. Agent流水线设计

### 3.1 Agent职责

#### Agent 1: 热点解读 (TrendInterpreter)

- 输入: 热点MD文本
- 输出: 结构化热点画像
- 职责:
  - 解析MD结构化内容
  - 提取核心事件、关键数据、争议点
  - 判断情绪倾向（正面/争议/焦虑/期待）
  - 识别可切入角度（至少3个）

#### Agent 2: 策略规划 (StrategyPlanner)

- 输入: 热点画像 + 目标平台列表
- 输出: 各平台内容策略卡
- 职责:
  - 结合热点画像与平台特性
  - 为每个平台制定: 选题角度、目标受众、内容结构（hook/body/CTA）、情绪共鸣点

#### Agent 3: 文案创作 (ContentWriter)

- 输入: 策略卡 + 平台风格模板
- 输出: 各平台完整初稿
- 平台适配:
  - 小红书: 种草逻辑、emoji节奏、分段标题
  - 微信: 深度观点、结构化论证、金句
  - 抖音: 前3秒hook、口语化、节奏感

#### Agent 4: 质量评审 (QualityReviewer)

- 输入: 各平台初稿
- 输出: 评审意见 + 评分
- 职责:
  - 平台调性一致性检查
  - 标题吸引力评分
  - 信息准确性校验
  - 敏感词/违规风险检测
- **条件循环**: 评分低于阈值 → 回流给ContentWriter修改（最多2次）

#### Agent 5: 终稿打磨 (FinalPolisher)

- 输入: 初稿 + 评审意见
- 输出: 最终定稿 + 多版标题
- 职责:
  - 根据评审意见修正
  - 添加话题标签、热门关键词
  - 生成多版本标题供选择

### 3.2 State模型

```python
class TrendProfile(BaseModel):
    core_event: str              # 核心事件
    key_data: list[str]          # 关键数据点
    sentiment: str               # 情绪倾向
    angles: list[str]            # 可切入角度

class PlatformStrategy(BaseModel):
    angle: str                   # 选题角度
    audience: str                # 目标受众
    structure: dict              # 内容结构（hook/body/cta）
    emotion_hook: str            # 情绪共鸣点

class PipelineState(BaseModel):
    # 输入
    trend_markdown: str                    # 热点MD原文
    platforms: list[str]                   # 目标平台
    style_override: str | None             # 自定义风格

    # Agent 1 输出
    trend_profile: TrendProfile | None

    # Agent 2 输出
    strategies: dict[str, PlatformStrategy]  # {平台: 策略卡}

    # Agent 3 输出
    drafts: dict[str, str]                   # {平台: 初稿}

    # Agent 4 输出
    review_feedback: dict[str, str]          # {平台: 评审意见}
    review_scores: dict[str, int]            # {平台: 评分}

    # Agent 5 输出
    final_content: dict[str, str]            # {平台: 终稿}
    title_options: dict[str, list[str]]      # {平台: 多版标题}

    # 运行指标
    metrics: PipelineMetrics
```

### 3.3 运行指标模型

```python
class AgentMetrics(BaseModel):
    agent_name: str
    duration_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int

class PipelineMetrics(BaseModel):
    agents: list[AgentMetrics]
    total_duration: float
    total_tokens: int
    average_score: float
    review_cycles: int        # 质检循环次数
```

---

## 4. CLI设计

### 4.1 两种使用模式

**直接命令模式:**
```bash
python main.py generate --input hotspot.md --platforms xiaohongshu,wechat,douyin
python main.py history --limit 10
python main.py model list
python main.py model use "DeepSeek"
python main.py config show
```

**交互式模式:**
```bash
python main.py
> /generate hotspot.md
> /history
> /model
```

### 4.2 内置命令列表

| 命令 | 说明 |
|------|------|
| `/generate [文件路径]` | 生成文案（可直接粘贴热点MD） |
| `/platform` | 查看/切换目标平台 |
| `/model` | 查看/切换模型源，支持添加/删除/测试连接 |
| `/template` | 管理风格模板 |
| `/history` | 查看生成历史 |
| `/review <id>` | 查看某次生成的详细指标 |
| `/export <id>` | 导出文案到文件 |
| `/stats` | 查看累计统计 |
| `/config` | 查看/修改配置 |
| `/help` | 显示帮助 |
| `/clear` | 清屏 |
| `/quit` | 退出 |

### 4.3 生成流程交互示例

```
> /generate hotspot.md

正在执行流水线...

━━━ Agent 1/5: 热点解读 ━━━
✓ 完成 (1.2s)
  模型: qwen-plus | tokens: 1,234 → 567 | 总计: 1,801

━━━ Agent 2/5: 策略规划 ━━━
✓ 完成 (2.1s)
  模型: qwen-plus | tokens: 2,100 → 1,890 | 总计: 3,990

━━━ Agent 3/5: 文案创作 ━━━
✓ 完成 (4.8s)
  模型: qwen-plus | tokens: 3,450 → 4,200 | 总计: 7,650

━━━ Agent 4/5: 质量评审 ━━━
✓ 完成 (1.5s)
  模型: qwen-plus | tokens: 5,100 → 890 | 总计: 5,990
  评审结果: 小红书 92 | 微信 88 | 抖音 95

━━━ Agent 5/5: 终稿打磨 ━━━
✓ 完成 (2.3s)
  模型: qwen-plus | tokens: 6,200 → 3,100 | 总计: 9,300

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 流水线完成

📊 运行摘要:
  总耗时: 11.9s
  总Token: 28,731 (输入 18,084 + 输出 10,647)
  平均评分: 91.7
  质检循环: 0次（首次通过）

--- 小红书 ---
标题: AI Agent到底有多强？实测后我惊了
正文: ...

--- 微信公众号 ---
标题: 深度解析：AI Agent如何改变我们的工作方式
正文: ...

--- 抖音 ---
脚本: 前3秒hook: "你还在自己写方案？AI已经能..."
```

---

## 5. 模型与配置

### 5.1 Model Provider

统一调用层，兼容OpenAI格式（百炼、DeepSeek等均兼容）。

```python
class ModelSource(BaseModel):
    name: str                # 自定义名称，如 "百炼千问"
    provider: str            # "openai_compatible"
    base_url: str            # API端点
    api_key: str
    model_name: str          # 如 "qwen-plus"
    is_active: bool          # 是否为当前使用的源

class ModelProvider:
    def __init__(self, source: ModelSource): ...
    def chat(self, messages: list, **kwargs) -> str: ...
```

### 5.2 多模型源管理

支持预配置多个模型源，一键切换当前使用的源。

**配置文件 (config.yaml):**

```yaml
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

  - name: "百炼千问Max"
    provider: "openai_compatible"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key: "sk-xxx"
    model_name: "qwen-max"
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

### 5.3 CLI模型管理命令

```bash
# 查看所有模型源
python main.py model list

# 输出:
#   名称           模型            状态
#   百炼千问       qwen-plus       ✓ 当前
#   DeepSeek       deepseek-chat
#   百炼千问Max    qwen-max

# 切换模型源
python main.py model use "DeepSeek"

# 添加新模型源
python main.py model add --name "智谱GLM" --base-url "https://open.bigmodel.cn/api/paas/v4" --api-key "sk-xxx" --model "glm-4"

# 修改当前源的API Key
python main.py model set-key sk-new-key

# 删除模型源
python main.py model remove "智谱GLM"
```

### 5.4 交互式模式模型命令

```
> /model

当前模型源: 百炼千问 (qwen-plus)

可用模型源:
  ✓ 百炼千问       qwen-plus        https://dashscope.aliyuncs.com/...
    DeepSeek       deepseek-chat    https://api.deepseek.com/...
    百炼千问Max    qwen-max         https://dashscope.aliyuncs.com/...

切换到: DeepSeek
✓ 已切换到 DeepSeek (deepseek-chat)

> /model add
? 模型源名称: 智谱GLM
? Base URL: https://open.bigmodel.cn/api/paas/v4
? API Key: sk-xxx
? 模型名称: glm-4
✓ 已添加模型源: 智谱GLM
```

### 5.5 Web界面模型管理

Web界面提供模型源管理页面：
- 列表展示所有已配置模型源（名称、模型、Base URL、状态）
- 切换当前源（点击切换按钮）
- 新增/编辑/删除模型源（表单弹窗）
- 测试连接（验证API Key是否有效）

---

## 6. 存储设计

### 6.1 SQLite表结构

```sql
-- 生成历史
CREATE TABLE generation_history (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    trend_markdown TEXT,
    platforms TEXT,            -- JSON array
    final_content TEXT,        -- JSON {platform: content}
    review_scores TEXT,        -- JSON {platform: score}
    total_tokens INTEGER,
    total_duration REAL,
    review_cycles INTEGER
);

-- Agent运行指标
CREATE TABLE agent_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation_id TEXT REFERENCES generation_history(id),
    agent_name TEXT,
    duration_seconds REAL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER
);

-- 风格模板
CREATE TABLE style_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    platform TEXT,
    prompt_template TEXT,
    created_at TIMESTAMP
);

-- 模型源配置
CREATE TABLE model_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    provider TEXT,
    base_url TEXT,
    api_key TEXT,
    model_name TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

### 6.2 统计功能

```bash
> /stats

📊 累计统计:
  总生成次数: 47
  总消耗Token: 1,234,567
  平均耗时: 13.2s
  平均评分: 90.3
  最常用平台: 小红书(42次) > 抖音(38次) > 微信(31次)
  质检循环率: 12.8% (6次需要修改)
```

---

## 7. 项目结构

```
content-forge/
├── src/
│   ├── agents/                    # Agent定义（纯业务逻辑）
│   │   ├── trend_interpreter.py
│   │   ├── strategy_planner.py
│   │   ├── content_writer.py
│   │   ├── quality_reviewer.py
│   │   └── final_polisher.py
│   │
│   ├── orchestrator/              # 流水线编排（可替换层）
│   │   ├── base.py                # 抽象接口
│   │   └── langgraph_impl.py     # LangGraph实现
│   │
│   ├── model/                     # 模型调用层
│   │   └── provider.py
│   │
│   ├── storage/                   # 存储层
│   │   ├── database.py
│   │   └── models.py             # Pydantic状态模型
│   │
│   ├── platforms/                 # 平台特性定义
│   │   └── profiles.py
│   │
│   └── cli/                       # CLI入口
│       └── main.py
│
├── config/
│   ├── config.yaml
│   └── prompts/                   # 各Agent的prompt模板
│       ├── trend_interpreter.md
│       ├── strategy_planner.md
│       ├── content_writer.md
│       ├── quality_reviewer.md
│       └── final_polisher.md
│
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

---

## 8. 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| Agent编排 | LangGraph | 流水线+条件循环天然支持，抽象接口可替换 |
| CLI框架 | Typer | 现代、类型安全、自动帮助文档 |
| 状态模型 | Pydantic v2 | 与框架解耦，类型校验 |
| 数据库 | SQLite + aiosqlite | 轻量，无需部署 |
| 模型调用 | OpenAI SDK兼容格式 | 百炼兼容，切换方便 |
| Prompt管理 | Markdown文件 | 易编辑、版本可控 |
| 配置 | YAML | 人类可读 |

---

## 9. 简历展示点

- 基于LangGraph的5-Agent流水线协作系统
- 支持LangGraph/自研双引擎，架构可扩展
- 条件质检循环（低分文案自动回流修改）
- 全链路Token追踪与运行指标统计
- 统一模型调用层，支持一键切换
- 交互式CLI，内置命令系统
