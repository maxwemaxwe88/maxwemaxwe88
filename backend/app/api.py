from __future__ import annotations

import time
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Request

from .collector import WINDOWS, Collector
from .config import SETTINGS
from .db import get_latest_snapshots, get_past_snapshot


router = APIRouter()


def _pct_change(latest: float, past: Optional[float]) -> Optional[float]:
    if past is None or past == 0:
        return None
    return (latest - past) / past * 100.0


@router.get("/health")
async def health():
    return {"ok": True}


@router.get("/exchanges")
async def exchanges(request: Request):
    # UI order = connector order.
    connectors = getattr(request.app.state, "connectors", None) or []
    names = []
    for c in connectors:
        n = getattr(c, "name", None)
        if isinstance(n, str):
            names.append(n)
    return {"exchanges": names}


def _collector_dep(request: Request) -> Collector:
    return request.app.state.collector


@router.get("/collector")
async def collector_state(collector: Collector = Depends(_collector_dep)):
    return {
        "settings": SETTINGS.model_dump(),
        "state": {k: v.__dict__ for k, v in collector.state.items()},
    }


@router.get("/oi")
async def oi(
    exchange: str = Query(..., description="Exchange name, e.g. binance"),
    sort_by: Literal["5m", "1h", "24h", "symbol"] = Query("5m"),
    order: Literal["desc", "asc"] = Query("desc"),
    limit: int = Query(50, ge=1, le=200),
):
    latest_rows = await get_latest_snapshots(SETTINGS.db_path, exchange)
    now = int(time.time())

    items = []
    for r in latest_rows:
        past_5m = await get_past_snapshot(SETTINGS.db_path, exchange, r.symbol, now - WINDOWS["5m"])
        past_1h = await get_past_snapshot(SETTINGS.db_path, exchange, r.symbol, now - WINDOWS["1h"])
        past_24h = await get_past_snapshot(SETTINGS.db_path, exchange, r.symbol, now - WINDOWS["24h"])

        ch_5m = _pct_change(r.oi, past_5m.oi if past_5m else None)
        ch_1h = _pct_change(r.oi, past_1h.oi if past_1h else None)
        ch_24h = _pct_change(r.oi, past_24h.oi if past_24h else None)

        items.append(
            {
                "exchange": r.exchange,
                "symbol": r.symbol,
                "ts": r.ts,
                "price": r.price,
                "oi": r.oi,
                "chg_5m": ch_5m,
                "chg_1h": ch_1h,
                "chg_24h": ch_24h,
            }
        )

    def sort_key(x):
        if sort_by == "symbol":
            return x["symbol"]
        v = x.get(f"chg_{sort_by}")
        # None values go to bottom regardless of order.
        return (v is None, v if v is not None else 0.0)

    reverse = order == "desc"
    items.sort(key=sort_key, reverse=reverse)
    return {"exchange": exchange, "items": items[:limit]}

