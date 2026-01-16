from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class KucoinFutures:
    """
    KuCoin Futures (USDT-margined). Public endpoint already includes openInterest per contract.
    """

    name = "kucoin"

    def __init__(self, session):
        self._session = session
        self._base = "https://api-futures.kucoin.com"
        self._cache: dict[str, tuple[float, float | None]] = {}

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        data = await get_json(self._session, f"{self._base}/api/v1/contracts/active")
        rows = (data or {}).get("data") or []
        items: list[SymbolInfo] = []
        self._cache.clear()
        for row in rows:
            sym = row.get("symbol")
            if not isinstance(sym, str):
                continue
            # Prefer USDT-margined symbols; KuCoin uses ...USDTM
            if not sym.endswith("USDTM"):
                continue
            try:
                vol = float(row.get("turnoverOf24h")) if row.get("turnoverOf24h") is not None else None
            except Exception:
                vol = None
            try:
                price = float(row.get("lastTradePrice")) if row.get("lastTradePrice") is not None else None
            except Exception:
                price = None
            oi_raw = row.get("openInterest")
            if oi_raw is None:
                continue
            try:
                oi = float(oi_raw)
            except Exception:
                continue
            self._cache[sym] = (oi, price)
            items.append(SymbolInfo(symbol=sym, volume_24h=vol, price=price))

        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        if symbol in self._cache:
            oi, price = self._cache[symbol]
            return OIQuote(symbol=symbol, oi=oi, price=price)
        # Fallback: refresh list once if cache missed
        await self.list_top_symbols(limit=1000)
        if symbol not in self._cache:
            raise RuntimeError(f"KuCoin symbol not found in contracts list: {symbol}")
        oi, price = self._cache[symbol]
        return OIQuote(symbol=symbol, oi=oi, price=price)

