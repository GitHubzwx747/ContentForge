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
