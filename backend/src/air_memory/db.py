"""SQLite 数据库初始化模块。"""

import aiosqlite

from air_memory.config import settings

# DDL：创建所有数据表
_DDL = """
CREATE TABLE IF NOT EXISTS save_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id     TEXT    NOT NULL,
    content       TEXT    NOT NULL,
    created_at    TEXT    NOT NULL,
    memory_deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS query_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    query      TEXT    NOT NULL,
    results    TEXT    NOT NULL,
    fast_only  INTEGER NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_values (
    memory_id      TEXT    PRIMARY KEY,
    value_score    REAL    NOT NULL DEFAULT 0.6,
    tier           TEXT    NOT NULL DEFAULT 'hot',
    feedback_count INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT    NOT NULL,
    updated_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id  TEXT    NOT NULL,
    valuable   INTEGER NOT NULL,
    created_at TEXT    NOT NULL
);
"""


async def init_db() -> None:
    """初始化 SQLite 数据库，创建所有数据表。"""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.executescript(_DDL)
        await db.commit()
