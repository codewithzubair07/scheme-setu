import json
from datetime import datetime, timezone

import aiosqlite


DB_PATH = "conversation.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations(
                user_id INTEGER,
                turn_index INTEGER,
                transcript TEXT,
                extracted_fields TEXT,
                response TEXT,
                timestamp TEXT
            )
            """
        )
        await db.commit()


async def save_turn(user_id: int, transcript: str, extracted_fields: dict, response: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COALESCE(MAX(turn_index), 0) FROM conversations WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        next_turn = (row[0] or 0) + 1
        await db.execute(
            """
            INSERT INTO conversations(user_id, turn_index, transcript, extracted_fields, response, timestamp)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                next_turn,
                transcript,
                json.dumps(extracted_fields, ensure_ascii=False),
                response,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        await db.commit()


async def get_last_fields(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT extracted_fields
            FROM conversations
            WHERE user_id = ?
            ORDER BY turn_index DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()

    if not row or not row[0]:
        return None
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return None