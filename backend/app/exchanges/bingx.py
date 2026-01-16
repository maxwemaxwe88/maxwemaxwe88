from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class BingxSwap:
    name = "bingx"

    def __init__(self, session):
        self._session = session
        self._base = "https://open-api.bingx.com"
        self._cache: dict[str, tuple[float | None, float | None]] = {}

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        data = await get_json(self._session, f"{self._base}/openApi/swap/v2/quote/ticker")
        rows = (data or {}).get("data") or []
        items: list[SymbolInfo] = []
        self._cache.clear()
        for row in rows:
            sym = row.get("symbol")
            if not isinstance(sym, str):
                continue
            if not sym.endswith("-USDT"):
                continue
            try:
                vol = float(row.get("quoteVolume")) if row.get("quoteVolume") is not None else None
            except Exception:
                vol = None
            try:
                price = float(row.get("lastPrice")) if row.get("lastPrice") is not None else None
            except Exception:
                price = None
            items.append(SymbolInfo(symbol=sym, volume_24h=vol, price=price))
            self._cache[sym] = (None, price)

        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        data = await get_json(
            self._session,
            f"{self._base}/openApi/swap/v2/quote/openInterest",
            params={"symbol": symbol},
        )
        d = (data or {}).get("data") or {}
        oi_raw = d.get("openInterest")
        if oi_raw is None:
            raise RuntimeError(f"BingX missing openInterest for {symbol}")
        oi = float(oi_raw)
        price = self._cache.get(symbol, (None, None))[1]
        return OIQuote(symbol=symbol, oi=oi, price=price)

