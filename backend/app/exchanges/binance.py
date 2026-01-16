from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class BinanceUsdM:
    name = "binance"

    def __init__(self, session):
        self._session = session
        self._base = "https://fapi.binance.com"

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        data = await get_json(self._session, f"{self._base}/fapi/v1/ticker/24hr")
        items: list[SymbolInfo] = []
        for row in data:
            sym = row.get("symbol")
            if not isinstance(sym, str):
                continue
            # USDT perpetuals only (rough filter; Binance uses same endpoint for USD-M)
            if not sym.endswith("USDT"):
                continue
            if "_" in sym:
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

        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        data = await get_json(
            self._session, f"{self._base}/fapi/v1/openInterest", params={"symbol": symbol}
        )
        oi_raw = data.get("openInterest")
        if oi_raw is None:
            raise RuntimeError(f"Binance missing openInterest for {symbol}")
        oi = float(oi_raw)
        return OIQuote(symbol=symbol, oi=oi, price=None)

