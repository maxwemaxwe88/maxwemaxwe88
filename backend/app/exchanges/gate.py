from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class GateUsdtFutures:
    """
    Gate.io USDT-settled futures.
    Uses /tickers for ranking and /contract_stats for open interest (USD).
    """

    name = "gate"

    def __init__(self, session):
        self._session = session
        self._base = "https://api.gateio.ws"
        self._cache: dict[str, tuple[float | None, float | None]] = {}

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        tickers = await get_json(self._session, f"{self._base}/api/v4/futures/usdt/tickers")
        items: list[SymbolInfo] = []
        self._cache.clear()
        for row in tickers:
            sym = row.get("contract")
            if not isinstance(sym, str):
                continue
            try:
                vol = float(row.get("volume_24h_quote")) if row.get("volume_24h_quote") is not None else None
            except Exception:
                vol = None
            try:
                price = float(row.get("last")) if row.get("last") is not None else None
            except Exception:
                price = None
            items.append(SymbolInfo(symbol=sym, volume_24h=vol, price=price))
            self._cache[sym] = (price, vol)

        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        # Gate provides OI via contract_stats. open_interest_usd is best for comparisons within exchange.
        stats = await get_json(
            self._session,
            f"{self._base}/api/v4/futures/usdt/contract_stats",
            params={"contract": symbol, "interval": "5m", "limit": 1},
        )
        if not stats:
            raise RuntimeError(f"Gate empty contract_stats for {symbol}")
        row = stats[0]
        oi_raw = row.get("open_interest_usd") or row.get("open_interest")
        if oi_raw is None:
            raise RuntimeError(f"Gate missing open_interest for {symbol}")
        oi = float(oi_raw)
        price = None
        if symbol in self._cache:
            price = self._cache[symbol][0]
        return OIQuote(symbol=symbol, oi=oi, price=price)

