from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from .config import SETTINGS
from .db import SnapshotRow, insert_snapshots, prune_old
from .exchanges.base import ExchangeConnector, SymbolInfo


WINDOWS: dict[str, int] = {"5m": 5 * 60, "1h": 60 * 60, "24h": 24 * 60 * 60}


@dataclass
class CollectorState:
    last_run_ts: int | None = None
    last_error: str | None = None


class Collector:
    def __init__(self, *, db_path: str, connectors: list[ExchangeConnector]):
        self._db_path = db_path
        self._connectors = connectors
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self.state: dict[str, CollectorState] = {c.name: CollectorState() for c in connectors}

    def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task

    async def _run_loop(self) -> None:
        interval = max(15, int(SETTINGS.fetch_interval_seconds))
        while not self._stop.is_set():
            t0 = time.time()
            await self._run_once()
            # keep ~interval cadence
            spent = time.time() - t0
            sleep_for = max(0.0, interval - spent)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=sleep_for)
            except TimeoutError:
                pass

    async def _run_once(self) -> None:
        # Run exchanges sequentially to be gentler on rate limits by default.
        for c in self._connectors:
            try:
                await self._collect_exchange(c)
                self.state[c.name].last_run_ts = int(time.time())
                self.state[c.name].last_error = None
            except Exception as e:
                self.state[c.name].last_error = repr(e)

        # prune in background best-effort
        try:
            await prune_old(self._db_path)
        except Exception:
            pass

    async def _collect_exchange(self, c: ExchangeConnector) -> None:
        symbols = await c.list_top_symbols(SETTINGS.max_symbols_per_exchange)
        ts = int(time.time())
        sem = asyncio.Semaphore(12)

        async def one(si: SymbolInfo) -> SnapshotRow | None:
            async with sem:
                try:
                    q = await c.fetch_open_interest(si.symbol)
                    price = q.price if q.price is not None else si.price
                    return SnapshotRow(exchange=c.name, symbol=si.symbol, ts=ts, oi=q.oi, price=price)
                except Exception:
                    return None

        rows = await asyncio.gather(*(one(si) for si in symbols))
        good = [r for r in rows if r is not None]
        if good:
            await insert_snapshots(self._db_path, good)

