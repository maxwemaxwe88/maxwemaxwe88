from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class BitgetUsdtFutures:
    name = "bitget"

    def __init__(self, session):
        self._session = session
        self._base = "https://api.bitget.com"
        self._cache: dict[str, tuple[float | None, float | None, float | None]] = {}
        # symbol -> (oi, price, volume)

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        data = await get_json(
            self._session,
            f"{self._base}/api/v2/mix/market/tickers",
            params={"productType": "USDT-FUTURES"},
        )
        rows = (data or {}).get("data") or []
        items: list[SymbolInfo] = []
        self._cache.clear()
        for row in rows:
            sym = row.get("symbol")
            if not isinstance(sym, str):
                continue
            if not sym.endswith("USDT"):
                continue
            try:
                vol = float(row.get("usdtVolume")) if row.get("usdtVolume") is not None else None
            except Exception:
                vol = None
            try:
                price = float(row.get("lastPr")) if row.get("lastPr") is not None else None
            except Exception:
                price = None
            # Bitget includes holdingAmount (open interest)
            oi = None
            if row.get("holdingAmount") is not None:
                try:
                    oi = float(row.get("holdingAmount"))
                except Exception:
                    oi = None
            items.append(SymbolInfo(symbol=sym, volume_24h=vol, price=price))
            self._cache[sym] = (oi, price, vol)

        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        if symbol in self._cache and self._cache[symbol][0] is not None:
            oi, price, _vol = self._cache[symbol]
            return OIQuote(symbol=symbol, oi=float(oi), price=price)

        data = await get_json(
            self._session,
            f"{self._base}/api/v2/mix/market/open-interest",
            params={"productType": "USDT-FUTURES", "symbol": symbol},
        )
        d = (data or {}).get("data") or {}
        lst = d.get("openInterestList") or []
        if not lst:
            raise RuntimeError(f"Bitget empty openInterestList for {symbol}")
        oi_raw = lst[0].get("size")
        if oi_raw is None:
            raise RuntimeError(f"Bitget missing size for {symbol}")
        oi = float(oi_raw)
        price = self._cache.get(symbol, (None, None, None))[1] if symbol in self._cache else None
        return OIQuote(symbol=symbol, oi=oi, price=price)

