from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class HtxUsdtSwap:
    """
    HTX (Huobi) USDT linear swaps.
    swap_open_interest without contract_code returns a bulk list for all swaps.
    """

    name = "htx"

    def __init__(self, session):
        self._session = session
        self._base = "https://api.hbdm.com"
        self._cache: dict[str, tuple[float, float | None, float | None]] = {}
        # symbol -> (oi_amount, price, turnover)

    async def _refresh(self) -> None:
        data = await get_json(self._session, f"{self._base}/linear-swap-api/v1/swap_open_interest")
        if (data or {}).get("status") != "ok":
            raise RuntimeError(f"HTX swap_open_interest status != ok: {data}")
        rows = data.get("data") or []
        self._cache.clear()
        for row in rows:
            code = row.get("contract_code")
            if not isinstance(code, str):
                continue
            # Prefer USDT swaps.
            if not code.endswith("-USDT"):
                continue
            oi_raw = row.get("amount")
            if oi_raw is None:
                continue
            try:
                oi = float(oi_raw)
            except Exception:
                continue
            # "trade_turnover" seems 24h turnover, keep for ranking.
            try:
                turnover = float(row.get("trade_turnover")) if row.get("trade_turnover") is not None else None
            except Exception:
                turnover = None
            self._cache[code] = (oi, None, turnover)

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        await self._refresh()
        items = [
            SymbolInfo(symbol=sym, volume_24h=(turnover or 0.0), price=None)
            for sym, (_oi, _price, turnover) in self._cache.items()
        ]
        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        if symbol not in self._cache:
            await self._refresh()
        if symbol not in self._cache:
            raise RuntimeError(f"HTX symbol not found: {symbol}")
        oi, price, _turnover = self._cache[symbol]
        # fetch price lazily from merged ticker
        if price is None:
            t = await get_json(
                self._session,
                f"{self._base}/linear-swap-ex/market/detail/merged",
                params={"contract_code": symbol},
            )
            if (t or {}).get("status") == "ok":
                try:
                    price = float(((t.get("tick") or {}).get("close")))
                except Exception:
                    price = None
            # update cache
            oi0, _p0, turnover0 = self._cache.get(symbol, (oi, None, None))
            self._cache[symbol] = (oi0, price, turnover0)
        return OIQuote(symbol=symbol, oi=oi, price=price)

