from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class BybitLinear:
    name = "bybit"

    def __init__(self, session):
        self._session = session
        self._base = "https://api.bybit.com"

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        data = await get_json(
            self._session,
            f"{self._base}/v5/market/tickers",
            params={"category": "linear"},
        )
        result = (data or {}).get("result") or {}
        rows = result.get("list") or []
        items: list[SymbolInfo] = []
        for row in rows:
            sym = row.get("symbol")
            if not isinstance(sym, str):
                continue
            # Keep typical USDT linear perps
            if not sym.endswith("USDT"):
                continue
            try:
                vol = float(row.get("turnover24h")) if row.get("turnover24h") is not None else None
            except Exception:
                vol = None
            try:
                price = float(row.get("lastPrice")) if row.get("lastPrice") is not None else None
            except Exception:
                price = None
            items.append(SymbolInfo(symbol=sym, volume_24h=vol, price=price))

        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        data = await get_json(
            self._session,
            f"{self._base}/v5/market/open-interest",
            params={"category": "linear", "symbol": symbol, "intervalTime": "5min"},
        )
        result = (data or {}).get("result") or {}
        rows = result.get("list") or []
        if not rows:
            raise RuntimeError(f"Bybit empty open-interest list for {symbol}")
        oi_raw = rows[0].get("openInterest")
        if oi_raw is None:
            raise RuntimeError(f"Bybit missing openInterest for {symbol}")
        oi = float(oi_raw)
        return OIQuote(symbol=symbol, oi=oi, price=None)

