from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .coinglass_client import gather_limited


@dataclass(frozen=True)
class OIChangeRow:
    symbol: str
    interval: str
    exchange: str | None
    oi_latest: float | None
    oi_prev: float | None
    oi_change: float | None
    oi_change_pct: float | None
    t_latest: Any | None
    t_prev: Any | None


def _as_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _extract_last_two_points(data: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Tries to normalize Coinglass OI history into two last points.

    Coinglass often returns:
    - {"data":[{"time":...,"openInterest":...}, ...]}
    - {"data":{"data":[...]}} (nested)
    - [{"time":...,"openInterest":...}, ...]
    """
    if data is None:
        return None, None

    series = None
    if isinstance(data, list):
        series = data
    elif isinstance(data, dict):
        if isinstance(data.get("data"), list):
            series = data["data"]
        elif isinstance(data.get("data"), dict) and isinstance(data["data"].get("data"), list):
            series = data["data"]["data"]
        elif isinstance(data.get("history"), list):
            series = data["history"]

    if not series or not isinstance(series, list):
        return None, None

    # assume already sorted by time asc; if not, sort best-effort
    try:
        series_sorted = sorted(series, key=lambda x: x.get("time") if isinstance(x, dict) else 0)
    except Exception:
        series_sorted = series

    if len(series_sorted) < 2:
        return (series_sorted[-1], None) if series_sorted else (None, None)

    return series_sorted[-1], series_sorted[-2]


def _extract_oi(point: dict[str, Any] | None) -> tuple[float | None, Any | None]:
    if not point:
        return None, None

    # Common field names across versions:
    # openInterest / oi / sumOpenInterest / open_interest
    oi = (
        point.get("openInterest")
        if "openInterest" in point
        else point.get("oi")
        if "oi" in point
        else point.get("sumOpenInterest")
        if "sumOpenInterest" in point
        else point.get("open_interest")
    )
    t = point.get("time") or point.get("timestamp") or point.get("date")
    return _as_float(oi), t


def compute_oi_change(
    *,
    symbol: str,
    interval: str,
    exchange: str | None,
    data: Any,
) -> OIChangeRow:
    latest, prev = _extract_last_two_points(data)
    oi_latest, t_latest = _extract_oi(latest)
    oi_prev, t_prev = _extract_oi(prev)

    if oi_latest is None or oi_prev is None:
        return OIChangeRow(
            symbol=symbol,
            interval=interval,
            exchange=exchange,
            oi_latest=oi_latest,
            oi_prev=oi_prev,
            oi_change=None,
            oi_change_pct=None,
            t_latest=t_latest,
            t_prev=t_prev,
        )

    change = oi_latest - oi_prev
    pct = (change / oi_prev * 100.0) if oi_prev != 0 else None
    return OIChangeRow(
        symbol=symbol,
        interval=interval,
        exchange=exchange,
        oi_latest=oi_latest,
        oi_prev=oi_prev,
        oi_change=change,
        oi_change_pct=pct,
        t_latest=t_latest,
        t_prev=t_prev,
    )


async def screen_open_interest(
    client: Any,
    *,
    symbols: Iterable[str],
    interval: str = "1h",
    exchange: str | None = None,
    limit_points: int = 50,
    endpoint_path: str = "open_interest_history",
    max_concurrency: int = 10,
) -> list[OIChangeRow]:
    sym_list = [s.strip().upper() for s in symbols if s and s.strip()]
    coros = [
        client.get_open_interest_history(
            symbol=s,
            interval=interval,
            exchange=exchange,
            limit=limit_points,
            endpoint_path=endpoint_path,
        )
        for s in sym_list
    ]
    results = await gather_limited(coros, max_concurrency=max_concurrency)
    rows: list[OIChangeRow] = []
    for s, data in zip(sym_list, results):
        rows.append(compute_oi_change(symbol=s, interval=interval, exchange=exchange, data=data))
    return rows


def filter_and_sort(
    rows: list[OIChangeRow],
    *,
    min_change_pct: float | None = None,
    max_change_pct: float | None = None,
    sort_by: str = "oi_change_pct",
    descending: bool = True,
    limit: int | None = 50,
) -> list[OIChangeRow]:
    def ok(r: OIChangeRow) -> bool:
        if r.oi_change_pct is None:
            return False
        if min_change_pct is not None and r.oi_change_pct < min_change_pct:
            return False
        if max_change_pct is not None and r.oi_change_pct > max_change_pct:
            return False
        return True

    filtered = [r for r in rows if ok(r)] if (min_change_pct is not None or max_change_pct is not None) else rows

    key = (lambda r: getattr(r, sort_by, None)) if sort_by in OIChangeRow.__dataclass_fields__ else (lambda r: r.oi_change_pct)
    filtered.sort(key=lambda r: (key(r) is None, key(r)), reverse=descending)
    return filtered[:limit] if limit else filtered

