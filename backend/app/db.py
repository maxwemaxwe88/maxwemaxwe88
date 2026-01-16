from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Iterable, Optional

import aiosqlite


@dataclass(frozen=True)
class SnapshotRow:
    exchange: str
    symbol: str
    ts: int
    oi: float
    price: Optional[float]


async def init_db(db_path: str) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS oi_snapshots (
              exchange TEXT NOT NULL,
              symbol   TEXT NOT NULL,
              ts       INTEGER NOT NULL,
              oi       REAL NOT NULL,
              price    REAL,
              PRIMARY KEY (exchange, symbol, ts)
            )
            """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_snapshots_lookup ON oi_snapshots(exchange, symbol, ts)"
        )
        await db.commit()


async def insert_snapshots(db_path: str, rows: Iterable[SnapshotRow]) -> int:
    inserted = 0
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        for r in rows:
            cur = await db.execute(
                """
                INSERT OR IGNORE INTO oi_snapshots(exchange, symbol, ts, oi, price)
                VALUES(?, ?, ?, ?, ?)
                """,
                (r.exchange, r.symbol, r.ts, r.oi, r.price),
            )
            inserted += cur.rowcount or 0
        await db.commit()
    return inserted


async def prune_old(db_path: str, keep_seconds: int = 26 * 3600) -> int:
    cutoff = int(time.time()) - keep_seconds
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("DELETE FROM oi_snapshots WHERE ts < ?", (cutoff,))
        await db.commit()
        return cur.rowcount or 0


async def get_latest_ts(db_path: str, exchange: str) -> Optional[int]:
    async with aiosqlite.connect(db_path) as db:
        row = await db.execute_fetchone(
            "SELECT MAX(ts) FROM oi_snapshots WHERE exchange = ?", (exchange,)
        )
        if not row:
            return None
        return row[0]


async def get_latest_snapshots(db_path: str, exchange: str) -> list[SnapshotRow]:
    async with aiosqlite.connect(db_path) as db:
        rows = await db.execute_fetchall(
            """
            SELECT s.exchange, s.symbol, s.ts, s.oi, s.price
            FROM oi_snapshots s
            JOIN (
              SELECT exchange, symbol, MAX(ts) AS ts
              FROM oi_snapshots
              WHERE exchange = ?
              GROUP BY exchange, symbol
            ) last
            ON s.exchange = last.exchange AND s.symbol = last.symbol AND s.ts = last.ts
            """,
            (exchange,),
        )
    return [SnapshotRow(*r) for r in rows]


async def get_past_snapshot(
    db_path: str, exchange: str, symbol: str, ts_lte: int
) -> Optional[SnapshotRow]:
    async with aiosqlite.connect(db_path) as db:
        row = await db.execute_fetchone(
            """
            SELECT exchange, symbol, ts, oi, price
            FROM oi_snapshots
            WHERE exchange = ? AND symbol = ? AND ts <= ?
            ORDER BY ts DESC
            LIMIT 1
            """,
            (exchange, symbol, ts_lte),
        )
    return SnapshotRow(*row) if row else None

