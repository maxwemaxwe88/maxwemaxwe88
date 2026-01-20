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

    async def list_futures_symbols(self, exchange: str, quote: str = "USDT") -> list[str]:
        """
        Return base symbols (coins) available on the exchange's USDT linear futures.

        - OKX: returns base coin for *-USDT-SWAP instruments (perpetual swaps)
        - Binance: returns baseAsset for USDT perpetual futures
        - Bybit: returns baseCoin for USDT linear instruments
        """
        ex = (exchange or "").strip().lower()
        if ex in {"okx", "okex"}:
            return await self._okx_list_usdt_swap_coins(quote=quote)
        if ex in {"binance", "binance futures", "binancefutures"}:
            return await self._binance_list_usdt_perp_coins(quote=quote)
        if ex in {"bybit"}:
            return await self._bybit_list_usdt_linear_coins(quote=quote)
        raise ExchangeError(f"Unsupported exchange '{exchange}' for listing futures.")

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

    async def _binance_list_usdt_perp_coins(self, quote: str = "USDT") -> list[str]:
        base = "https://fapi.binance.com"
        url = f"{base}/fapi/v1/exchangeInfo"
        r = await self._client.get(url)
        if r.status_code >= 400:
            raise ExchangeError(f"Binance exchangeInfo status {r.status_code}: {r.text[:300]}")
        payload = r.json()
        symbols = payload.get("symbols") if isinstance(payload, dict) else None
        if not isinstance(symbols, list):
            raise ExchangeError(f"Binance unexpected exchangeInfo: {str(payload)[:300]}")

        out: set[str] = set()
        for s in symbols:
            if not isinstance(s, dict):
                continue
            if s.get("status") != "TRADING":
                continue
            if s.get("contractType") != "PERPETUAL":
                continue
            if (s.get("quoteAsset") or "").upper() != quote.upper():
                continue
            base_asset = (s.get("baseAsset") or "").upper()
            if base_asset:
                out.add(base_asset)
        return sorted(out)

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

    async def _bybit_list_usdt_linear_coins(self, quote: str = "USDT") -> list[str]:
        base = "https://api.bybit.com"
        url = f"{base}/v5/market/instruments-info"
        cursor: str | None = None
        out: set[str] = set()
        # paginate a few pages defensively
        for _ in range(10):
            params: dict[str, Any] = {"category": "linear", "limit": 1000}
            if cursor:
                params["cursor"] = cursor
            r = await self._client.get(url, params=params)
            if r.status_code >= 400:
                raise ExchangeError(f"Bybit instruments status {r.status_code}: {r.text[:300]}")
            payload = r.json()
            if not isinstance(payload, dict) or payload.get("retCode") not in (0, "0", None):
                raise ExchangeError(f"Bybit instruments error: {payload.get('retCode')} {payload.get('retMsg')}")
            result = payload.get("result") or {}
            items = result.get("list") or []
            if not isinstance(items, list):
                raise ExchangeError(f"Bybit instruments unexpected: {str(payload)[:300]}")
            for it in items:
                if not isinstance(it, dict):
                    continue
                if (it.get("quoteCoin") or "").upper() != quote.upper():
                    continue
                # "status" can be "Trading"
                st = (it.get("status") or "").lower()
                if st and st not in {"trading"}:
                    continue
                base_coin = (it.get("baseCoin") or "").upper()
                if base_coin:
                    out.add(base_coin)
            cursor = result.get("nextPageCursor") or None
            if not cursor:
                break
        return sorted(out)

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

    async def _okx_list_usdt_swap_coins(self, quote: str = "USDT") -> list[str]:
        base = "https://www.okx.com"
        url = f"{base}/api/v5/public/instruments"
        # instType supports SWAP/FUTURES; we use SWAP because it's the closest to USDT perpetual futures
        params = {"instType": "SWAP"}
        r = await self._client.get(url, params=params)
        if r.status_code >= 400:
            raise ExchangeError(f"OKX instruments status {r.status_code}: {r.text[:300]}")
        payload = r.json()
        if not isinstance(payload, dict) or payload.get("code") != "0":
            raise ExchangeError(f"OKX instruments error: {str(payload)[:300]}")
        data = payload.get("data") or []
        if not isinstance(data, list):
            raise ExchangeError(f"OKX instruments unexpected: {str(payload)[:300]}")

        suffix = f"-{quote.upper()}-SWAP"
        out: set[str] = set()
        for it in data:
            if not isinstance(it, dict):
                continue
            inst_id = (it.get("instId") or "").upper()
            if not inst_id.endswith(suffix):
                continue
            base_coin = inst_id.split("-")[0].strip().upper()
            if base_coin:
                out.add(base_coin)
        return sorted(out)

