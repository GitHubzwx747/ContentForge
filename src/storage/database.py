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
        stats = dict(zip(columns, row))

        # Compute avg_score from JSON review_scores
        cursor2 = await self._db.execute(
            "SELECT review_scores FROM generation_history WHERE review_scores IS NOT NULL"
        )
        rows = await cursor2.fetchall()
        all_scores = []
        for (rs,) in rows:
            if not rs:
                continue
            try:
                scores = json.loads(rs) if isinstance(rs, str) else rs
                if isinstance(scores, dict):
                    all_scores.extend(v for v in scores.values() if isinstance(v, (int, float)))
            except (json.JSONDecodeError, TypeError):
                pass
        stats["avg_score"] = round(sum(all_scores) / len(all_scores)) if all_scores else 0
        return stats
