from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from .coinglass_client import CoinglassClient, CoinglassError
from .screener import filter_and_sort, screen_open_interest


app = FastAPI(title="Coinglass Open Interest Screener", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/screener")
async def screener(
    symbols: str = Query(..., description="Comma-separated symbols, e.g. BTC,ETH,SOL"),
    interval: str = Query("1h", description="Interval: 5m/15m/1h/4h/1d etc (depends on Coinglass)"),
    exchange: str | None = Query(None, description="Optional exchange name, e.g. Binance"),
    min_change_pct: float | None = Query(None, description="Min OI change %"),
    max_change_pct: float | None = Query(None, description="Max OI change %"),
    limit: int = Query(50, ge=1, le=500),
    endpoint_path: str = Query("open_interest_history", description="Override Coinglass endpoint path"),
    max_concurrency: int = Query(10, ge=1, le=50),
) -> dict:
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        raise HTTPException(status_code=400, detail="No symbols provided")

    client = CoinglassClient()
    try:
        rows = await screen_open_interest(
            client,
            symbols=sym_list,
            interval=interval,
            exchange=exchange,
            endpoint_path=endpoint_path,
            max_concurrency=max_concurrency,
        )
        rows = filter_and_sort(
            rows,
            min_change_pct=min_change_pct,
            max_change_pct=max_change_pct,
            limit=limit,
        )
        return {
            "interval": interval,
            "exchange": exchange,
            "count": len(rows),
            "rows": [r.__dict__ for r in rows],
        }
    except CoinglassError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    finally:
        await client.aclose()

