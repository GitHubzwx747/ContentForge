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
            trend_markdown=f"test {i}",
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
