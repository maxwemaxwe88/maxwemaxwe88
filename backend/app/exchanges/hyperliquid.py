from __future__ import annotations

from .base import OIQuote, SymbolInfo

import aiohttp


class HyperliquidPerps:
    """
    Hyperliquid perps (on-chain). Uses bulk metaAndAssetCtxs call.
    """

    name = "hyperliquid"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._url = "https://api.hyperliquid.xyz/info"
        self._cache: dict[str, tuple[float, float | None, float | None]] = {}
        # coin -> (openInterest, markPx, dayNtlVlm)

    async def _refresh(self) -> None:
        async with self._session.post(self._url, json={"type": "metaAndAssetCtxs"}) as resp:
            resp.raise_for_status()
            payload = await resp.json()
        if not isinstance(payload, list) or len(payload) != 2:
            raise RuntimeError("Hyperliquid unexpected response shape")
        meta, ctxs = payload
        universe = (meta or {}).get("universe") or []
        if not isinstance(universe, list) or not isinstance(ctxs, list):
            raise RuntimeError("Hyperliquid invalid meta/ctxs types")

        self._cache.clear()
        # ctxs align by index to universe assets.
        for i, u in enumerate(universe):
            try:
                coin = u.get("name")
            except Exception:
                coin = None
            if not isinstance(coin, str) or i >= len(ctxs):
                continue
            c = ctxs[i]
            oi_raw = c.get("openInterest")
            if oi_raw is None:
                continue
            try:
                oi = float(oi_raw)
            except Exception:
                continue
            try:
                px = float(c.get("markPx")) if c.get("markPx") is not None else None
            except Exception:
                px = None
            try:
                vol = float(c.get("dayNtlVlm")) if c.get("dayNtlVlm") is not None else None
            except Exception:
                vol = None
            # Use coin as symbol (short, readable).
            self._cache[coin] = (oi, px, vol)

    async def list_top_symbols(self, limit: int) -> list[SymbolInfo]:
        await self._refresh()
        items = [
            SymbolInfo(symbol=coin, volume_24h=(vol or 0.0), price=px)
            for coin, (_oi, px, vol) in self._cache.items()
        ]
        items.sort(key=lambda x: (x.volume_24h or 0.0), reverse=True)
        return items[:limit]

    async def fetch_open_interest(self, symbol: str) -> OIQuote:
        if symbol not in self._cache:
            await self._refresh()
        if symbol not in self._cache:
            raise RuntimeError(f"Hyperliquid coin not found: {symbol}")
        oi, px, _vol = self._cache[symbol]
        return OIQuote(symbol=symbol, oi=oi, price=px)

