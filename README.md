# ContentForge

多智能体文案生成系统，基于 LangGraph 编排的 5-Agent 流水线，将热点信息自动生成适配多平台的爆款文案。

## 特性

- 🔥 **多平台适配**: 一键生成小红书、微信公众号、抖音文案
- 🤖 **5-Agent 流水线**: 热点解读 → 策略规划 → 文案创作 → 质量评审 → 终稿打磨
- 🔄 **质检循环**: 低分文案自动回流修改，确保质量
- 📊 **全链路追踪**: Token 消耗、运行时长、评分等完整指标
- 🎛️ **灵活扩展**: 编排层抽象接口，支持未来替换为自研框架
- 💻 **双端支持**: 交互式 CLI + 现代 Web 界面
- 🔌 **多模型源**: 统一调用层，支持一键切换 OpenAI/百炼/DeepSeek 等

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| Agent 编排 | LangGraph |
| CLI 框架 | Typer |
| 状态模型 | Pydantic v2 |
| 数据库 | SQLite + aiosqlite |
| Web 后端 | FastAPI |
| Web 前端 | React + Vite |
| 模型调用 | OpenAI SDK 兼容格式 |

## 项目结构

```
content-forge/
├── src/
│   ├── agents/              # Agent 定义（纯业务逻辑）
│   │   ├── trend_interpreter.py
│   │   ├── strategy_planner.py
│   │   ├── content_writer.py
│   │   ├── quality_reviewer.py
│   │   └── final_polisher.py
│   ├── orchestrator/        # 流水线编排（可替换层）
│   │   ├── base.py          # 抽象接口
│   │   └── langgraph_impl.py
│   ├── model/               # 模型调用层
│   ├── storage/             # 存储层
│   ├── platforms/           # 平台特性定义
│   ├── cli/                 # CLI 入口
│   └── web/                 # Web 后端
├── frontend/                # React 前端
├── config/                  # 配置和 Prompts
├── tests/                   # 测试
├── docs/                    # 文档
└── pyproject.toml
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+

### 后端安装

```bash
# 克隆项目
git clone <repo-url>
cd content-forge

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -e .
```

### 前端安装

```bash
cd frontend
npm install
```

### 配置

复制 `config/config.yaml` 并配置你的模型源：

```yaml
model_sources:
  - name: "百炼千问"
    provider: "openai_compatible"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key: "your-api-key"
    model_name: "qwen-plus"
    is_active: true

review:
  score_threshold: 85
  max_cycles: 2

default_platforms:
  - xiaohongshu
  - wechat
  - douyin
```

## 使用

### CLI 模式

```bash
# 直接命令模式
python -m src.cli.main generate --input hotspot.md --platforms xiaohongshu,wechat

# 交互式模式
python -m src.cli.main
```

### Web 模式

```bash
# 启动后端
python -m src.web.app

# 启动前端（新终端）
cd frontend
npm run dev
```

访问 http://localhost:5173

## Agent 流水线

1. **热点解读**: 解析热点文本，提取核心事件、情绪倾向、切入角度
2. **策略规划**: 结合平台特性，制定内容策略卡
3. **文案创作**: 生成各平台初稿
4. **质量评审**: 评分与反馈，低分自动回流修改（最多 2 次）
5. **终稿打磨**: 优化文案，生成多版标题

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

## 许可证

MIT
