from __future__ import annotations

from .base import OIQuote, SymbolInfo
from ..http import get_json


class OkxSwap:
    name = "okx"

    def __init__(self, session):
        self._session = session
        self._base = "https://www.okx.com"

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        data = await get_json(
            self._session,
            f"{self._base}/api/v5/market/tickers",
            params={"instType": "SWAP"},
        )
        rows = (data or {}).get("data") or []
        items: list[SymbolInfo] = []
        for row in rows:
            inst = row.get("instId")
            if not isinstance(inst, str):
                continue
            # Prefer USDT swaps (e.g., BTC-USDT-SWAP)
            if "-USDT-" not in inst:
                continue
            try:
                vol = float(row.get("volCcy24h")) if row.get("volCcy24h") is not None else None
            except Exception:
                try:
                    vol = float(row.get("vol24h")) if row.get("vol24h") is not None else None
                except Exception:
                    vol = None
            try:
                price = float(row.get("last")) if row.get("last") is not None else None
            except Exception:
                price = None
            items.append(SymbolInfo(symbol=inst, volume_24h=vol, price=price))

        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        data = await get_json(
            self._session,
            f"{self._base}/api/v5/public/open-interest",
            params={"instType": "SWAP", "instId": symbol},
        )
        rows = (data or {}).get("data") or []
        if not rows:
            raise RuntimeError(f"OKX empty open-interest for {symbol}")
        row = rows[0]
        oi_raw = row.get("oi")
        if oi_raw is None:
            raise RuntimeError(f"OKX missing oi for {symbol}")
        oi = float(oi_raw)
        return OIQuote(symbol=symbol, oi=oi, price=None)

