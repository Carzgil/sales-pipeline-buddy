import aiosqlite
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "sales_buddy.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS briefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_name TEXT NOT NULL,
                city TEXT NOT NULL,
                brief_json TEXT NOT NULL,
                fit_signal TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scorecards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_name TEXT NOT NULL,
                transcript_hash TEXT NOT NULL UNIQUE,
                scorecard_json TEXT NOT NULL,
                coaching_note TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def save_brief(restaurant_name: str, city: str, brief_json: dict, fit_signal: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO briefs (restaurant_name, city, brief_json, fit_signal, created_at) VALUES (?, ?, ?, ?, ?)",
            (restaurant_name, city, json.dumps(brief_json), fit_signal, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def save_scorecard(
    restaurant_name: str,
    transcript_hash: str,
    scorecard_json: dict,
    coaching_note: str,
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM scorecards WHERE transcript_hash = ?", (transcript_hash,)
        )
        if await cursor.fetchone():
            return
        await db.execute(
            "INSERT INTO scorecards (restaurant_name, transcript_hash, scorecard_json, coaching_note, created_at) VALUES (?, ?, ?, ?, ?)",
            (restaurant_name, transcript_hash, json.dumps(scorecard_json), coaching_note, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_recent_briefs(limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM briefs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "restaurant_name": row["restaurant_name"],
                "city": row["city"],
                "brief": json.loads(row["brief_json"]),
                "fit_signal": row["fit_signal"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


async def get_recent_scorecards(limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM scorecards ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "restaurant_name": row["restaurant_name"],
                "scorecard": json.loads(row["scorecard_json"]),
                "coaching_note": row["coaching_note"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
