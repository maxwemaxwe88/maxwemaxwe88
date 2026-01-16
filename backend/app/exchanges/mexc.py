from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class MexcPerpetual:
    """
    MEXC contract API (USDT perpetuals). Ticker includes holdVol which we use as OI proxy.
    """

    name = "mexc"

    def __init__(self, session):
        self._session = session
        self._base = "https://contract.mexc.com"
        self._cache: dict[str, tuple[float | None, float | None]] = {}

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        data = await get_json(self._session, f"{self._base}/api/v1/contract/ticker")
        rows = (data or {}).get("data") or []
        items: list[SymbolInfo] = []
        self._cache.clear()
        for row in rows:
            sym = row.get("symbol")
            if not isinstance(sym, str):
                continue
            if not sym.endswith("_USDT"):
                continue
            try:
                vol = float(row.get("amount24")) if row.get("amount24") is not None else None
            except Exception:
                vol = None
            try:
                price = float(row.get("lastPrice")) if row.get("lastPrice") is not None else None
            except Exception:
                price = None
            oi = None
            if row.get("holdVol") is not None:
                try:
                    oi = float(row.get("holdVol"))
                except Exception:
                    oi = None
            items.append(SymbolInfo(symbol=sym, volume_24h=vol, price=price))
            if oi is not None:
                self._cache[sym] = (oi, price)

        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        if symbol in self._cache:
            oi, price = self._cache[symbol]
            return OIQuote(symbol=symbol, oi=float(oi), price=price)
        # Fallback: refresh once
        await self.list_top_symbols(limit=1000)
        if symbol not in self._cache:
            raise RuntimeError(f"MEXC symbol not found or missing holdVol: {symbol}")
        oi, price = self._cache[symbol]
        return OIQuote(symbol=symbol, oi=float(oi), price=price)

