from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings, get_settings


class CoinglassError(RuntimeError):
    pass


@dataclass(frozen=True)
class CoinglassResponse:
    raw: dict[str, Any]

    @property
    def code(self) -> Any:
        return self.raw.get("code")

    @property
    def msg(self) -> str | None:
        return self.raw.get("msg") or self.raw.get("message")

    @property
    def data(self) -> Any:
        # Coinglass usually returns {"code":"0","msg":"success","data": ...}
        return self.raw.get("data", self.raw)


class CoinglassClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        headers: dict[str, str] = {}
        if self.settings.api_key:
            # Many Coinglass setups use `coinglassSecret`, but some versions/plans use different header names.
            # If user explicitly sets COINGLASS_API_KEY_HEADER, honor only that.
            if self.settings.api_key_headers and self.settings.api_key_header == "coinglassSecret":
                for h in [x.strip() for x in self.settings.api_key_headers.split(",") if x.strip()]:
                    headers[h] = self.settings.api_key
            else:
                headers[self.settings.api_key_header] = self.settings.api_key

        self._client = httpx.AsyncClient(
            base_url=self.settings.api_base_url.rstrip("/"),
            headers=headers,
            timeout=self.settings.timeout_s,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> CoinglassResponse:
        """
        Generic GET wrapper.

        You can override endpoints via `path` if Coinglass changes naming.
        """
        url = path if path.startswith("/") else f"/{path}"
        try:
            r = await self._client.get(url, params=params)
        except httpx.HTTPError as e:
            raise CoinglassError(f"Coinglass HTTP error: {e}") from e

        if r.status_code >= 400:
            raise CoinglassError(f"Coinglass bad status {r.status_code}: {r.text}")

        try:
            payload = r.json()
        except ValueError as e:
            raise CoinglassError(f"Coinglass invalid JSON: {r.text[:500]}") from e

        resp = CoinglassResponse(raw=payload if isinstance(payload, dict) else {"data": payload})
        # Coinglass typically uses code "0" for success; be permissive otherwise.
        if resp.code not in (None, 0, "0", "200", 200):
            raise CoinglassError(f"Coinglass API error code={resp.code} msg={resp.msg}")
        return resp

    async def get_open_interest_history(
        self,
        symbol: str,
        interval: str = "1h",
        exchange: str | None = None,
        limit: int = 50,
        endpoint_path: str = "openInterestHistory",
    ) -> Any:
        """
        Fetch OI history.

        Coinglass endpoint naming differs by API version/plan.
        Default path: /openInterestHistory

        Coinglass parameter naming differs by API version/plan as well.
        We try a small set of common variants and return the first successful response.
        """
        endpoint_candidates = [
            endpoint_path,
            # common alternates seen in different Open API versions:
            "futures/openInterestHistory",
            "openInterestHistory",
        ]

        param_candidates: list[dict[str, Any]] = []
        interval_candidates = list(dict.fromkeys([interval, interval.upper()]))
        if interval.lower() in ("5m", "5min"):
            interval_candidates += ["5min", "5m"]
        if interval.lower() in ("1h", "60m"):
            interval_candidates += ["60m", "1h", "1H"]
        if interval.lower() in ("1d", "24h", "24H"):
            interval_candidates += ["1d", "24h", "1D"]
        interval_candidates = list(dict.fromkeys([x for x in interval_candidates if x]))

        # Variant A: symbol + exchange
        for iv in interval_candidates:
            p1: dict[str, Any] = {"symbol": symbol, "interval": iv, "limit": limit}
            if exchange:
                p1["exchange"] = exchange
            param_candidates.append(p1)

            # Variant B: symbol + exchangeName
            p2: dict[str, Any] = {"symbol": symbol, "interval": iv, "limit": limit}
            if exchange:
                p2["exchangeName"] = exchange
            param_candidates.append(p2)

            # Variant C: coin + exchange
            p3: dict[str, Any] = {"coin": symbol, "interval": iv, "limit": limit}
            if exchange:
                p3["exchange"] = exchange
            param_candidates.append(p3)

            # Variant D: coin + exchangeName
            p4: dict[str, Any] = {"coin": symbol, "interval": iv, "limit": limit}
            if exchange:
                p4["exchangeName"] = exchange
            param_candidates.append(p4)

            # Variant E: symbol only (some endpoints don't accept exchange)
            p5: dict[str, Any] = {"symbol": symbol, "interval": iv, "limit": limit}
            param_candidates.append(p5)

            # Variant F: coin only
            p6: dict[str, Any] = {"coin": symbol, "interval": iv, "limit": limit}
            param_candidates.append(p6)

        last_err: Exception | None = None
        for ep in endpoint_candidates:
            for params in param_candidates:
                try:
                    return (await self.get(ep, params=params)).data
                except CoinglassError as e:
                    last_err = e
                    continue

        raise CoinglassError(
            f"Coinglass OI history failed for symbol={symbol} interval={interval} exchange={exchange}: {last_err}"
        ) from last_err


async def gather_limited(
    coros: list[asyncio.Future],
    max_concurrency: int = 10,
) -> list[Any]:
    sem = asyncio.Semaphore(max_concurrency)

    async def _run(coro: asyncio.Future) -> Any:
        async with sem:
            return await coro

    return await asyncio.gather(*[_run(c) for c in coros])

