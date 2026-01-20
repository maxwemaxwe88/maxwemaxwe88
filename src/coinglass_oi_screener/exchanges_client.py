from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class ExchangeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExchangeOIHistoryPoint:
    time: int | None
    open_interest: float | None


def _as_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _sym_usdt(coin: str) -> str:
    c = coin.strip().upper()
    # Allow users to pass BTCUSDT already
    return c if c.endswith("USDT") else f"{c}USDT"


class ExchangeOIClient:
    """
    Public (no-key) OI history client for supported exchanges.

    Supported:
    - Binance futures: /futures/data/openInterestHist
    - Bybit v5: /v5/market/open-interest
    - OKX: /api/v5/rubik/stat/contracts/open-interest-volume
    """

    def __init__(self, timeout_s: float = 20.0) -> None:
        self._timeout = timeout_s
        self._client = httpx.AsyncClient(timeout=timeout_s)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_open_interest_history(
        self,
        symbol: str,
        interval: str = "1h",
        exchange: str | None = None,
        limit: int = 50,
        endpoint_path: str | None = None,  # kept for compatibility; ignored here
    ) -> Any:
        ex = (exchange or "binance").strip().lower()
        if ex in {"binance", "binance futures", "binancefutures"}:
            return await self._binance_open_interest_hist(symbol=symbol, interval=interval, limit=limit)
        if ex in {"bybit"}:
            return await self._bybit_open_interest_hist(symbol=symbol, interval=interval, limit=limit)
        if ex in {"okx", "okex"}:
            return await self._okx_open_interest_hist(symbol=symbol, interval=interval, limit=limit)
        raise ExchangeError(
            f"Unsupported exchange '{exchange}'. Supported: OKX, Binance, Bybit (case-insensitive)."
        )

    async def _binance_open_interest_hist(self, symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
        """
        Binance futures open interest history.
        Docs: https://binance-docs.github.io/apidocs/futures/en/#open-interest-statistics
        """
        base = "https://fapi.binance.com"
        period = interval
        if interval.lower() == "24h":
            period = "1d"
        params = {
            "symbol": _sym_usdt(symbol),
            "period": period,
            "limit": min(max(limit, 2), 500),
        }
        url = f"{base}/futures/data/openInterestHist"
        r = await self._client.get(url, params=params)
        if r.status_code >= 400:
            # Common case: 451 restricted location
            raise ExchangeError(f"Binance bad status {r.status_code}: {r.text[:500]}")
        data = r.json()
        if not isinstance(data, list):
            raise ExchangeError(f"Binance unexpected response: {str(data)[:500]}")

        # Normalize to our internal "Coinglass-like" series dicts
        out: list[dict[str, Any]] = []
        for p in data:
            if not isinstance(p, dict):
                continue
            out.append(
                {
                    "time": int(p.get("timestamp")) if p.get("timestamp") is not None else None,
                    # Binance uses sumOpenInterest
                    "openInterest": _as_float(p.get("sumOpenInterest") or p.get("openInterest")),
                }
            )
        return out

    async def _bybit_open_interest_hist(self, symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
        """
        Bybit v5 open interest.
        Docs (public): https://bybit-exchange.github.io/docs/v5/market/open-interest
        """
        base = "https://api.bybit.com"
        # Bybit uses intervalTime: 5min/15min/1h/4h/1d
        iv = interval
        if interval.lower() == "5m":
            iv = "5min"
        if interval.lower() == "24h":
            iv = "1d"
        params = {
            "category": "linear",
            "symbol": _sym_usdt(symbol),
            "intervalTime": iv,
            "limit": min(max(limit, 2), 200),
        }
        url = f"{base}/v5/market/open-interest"
        r = await self._client.get(url, params=params)
        if r.status_code >= 400:
            # Common case: 403 CloudFront country block
            raise ExchangeError(f"Bybit bad status {r.status_code}: {r.text[:500]}")
        payload = r.json()
        if not isinstance(payload, dict):
            raise ExchangeError(f"Bybit unexpected response: {str(payload)[:500]}")
        if payload.get("retCode") not in (0, "0", None):
            raise ExchangeError(f"Bybit API error: {payload.get('retCode')} {payload.get('retMsg')}")

        result = payload.get("result") or {}
        series = result.get("list") or []
        if not isinstance(series, list):
            raise ExchangeError(f"Bybit unexpected series: {str(series)[:500]}")

        out: list[dict[str, Any]] = []
        for p in series:
            if not isinstance(p, dict):
                continue
            # Bybit list items often have "openInterest" and "timestamp" (ms)
            ts = p.get("timestamp") or p.get("time")
            try:
                ts_i = int(ts) if ts is not None else None
            except (TypeError, ValueError):
                ts_i = None
            out.append(
                {
                    "time": ts_i,
                    "openInterest": _as_float(p.get("openInterest") or p.get("open_interest")),
                }
            )
        return out

    async def _okx_open_interest_hist(self, symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
        """
        OKX Rubik open interest volume endpoint.
        Period supports: 5m, 1H, 1D (matches our UI 5m/1h/24h).
        """
        base = "https://www.okx.com"
        period = interval
        if interval.lower() == "1h":
            period = "1H"
        if interval.lower() in {"24h", "1d"}:
            period = "1D"
        if interval.lower() == "5m":
            period = "5m"

        url = f"{base}/api/v5/rubik/stat/contracts/open-interest-volume"
        params = {"ccy": symbol.strip().upper(), "period": period}
        r = await self._client.get(url, params=params)
        if r.status_code >= 400:
            raise ExchangeError(f"OKX bad status {r.status_code}: {r.text[:500]}")
        payload = r.json()
        if not isinstance(payload, dict) or payload.get("code") != "0":
            raise ExchangeError(f"OKX API error: {str(payload)[:500]}")
        series = payload.get("data") or []
        if not isinstance(series, list):
            raise ExchangeError(f"OKX unexpected series: {str(series)[:500]}")

        # Data rows are arrays: [ts, oi, vol] (strings). We'll use oi.
        out: list[dict[str, Any]] = []
        for row in series[: max(2, min(limit, 200))]:
            if not isinstance(row, list) or len(row) < 2:
                continue
            try:
                ts_i = int(row[0])
            except (TypeError, ValueError):
                ts_i = None
            out.append({"time": ts_i, "openInterest": _as_float(row[1])})
        return out

