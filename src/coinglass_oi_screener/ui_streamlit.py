from __future__ import annotations

import asyncio
from typing import Any

import streamlit as st

from .coinglass_client import CoinglassClient, CoinglassError
from .screener import filter_and_sort, screen_open_interest


def _rows_to_dicts(rows) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "symbol": r.symbol,
                "oi_latest": r.oi_latest,
                "oi_prev": r.oi_prev,
                "oi_change": r.oi_change,
                "oi_change_pct": r.oi_change_pct,
                "t_latest": r.t_latest,
                "t_prev": r.t_prev,
            }
        )
    return out


def _run_async(coro):
    # Streamlit runs in a normal sync context; safe to run our async pipeline per interaction.
    return asyncio.run(coro)


async def _screen(
    symbols: list[str],
    interval: str,
    exchange: str | None,
    endpoint_path: str,
    max_concurrency: int,
    min_change_pct: float | None,
    max_change_pct: float | None,
    limit: int,
    descending: bool,
):
    client = CoinglassClient()
    try:
        rows = await screen_open_interest(
            client,
            symbols=symbols,
            interval=interval,
            exchange=exchange,
            endpoint_path=endpoint_path,
            max_concurrency=max_concurrency,
        )
        return filter_and_sort(
            rows,
            min_change_pct=min_change_pct,
            max_change_pct=max_change_pct,
            limit=limit,
            descending=descending,
        )
    finally:
        await client.aclose()


def main() -> None:
    st.set_page_config(page_title="Coinglass OI Screener", layout="wide")

    st.title("Coinglass Open Interest Screener")
    st.caption("Быстрый визуальный скринер изменения OI по последним двум точкам истории.")

    with st.sidebar:
        st.subheader("Параметры")
        symbols_raw = st.text_input("Symbols (через запятую)", value="BTC,ETH,SOL")
        interval = st.text_input("Interval", value="1h")
        exchange = st.text_input("Exchange (опционально)", value="")
        endpoint_path = st.text_input("Endpoint path", value="openInterestHistory")
        max_concurrency = st.slider("Concurrency", min_value=1, max_value=50, value=10)
        limit = st.slider("Limit", min_value=1, max_value=500, value=50)
        descending = st.checkbox("Sort desc (largest Δ%)", value=True)
        min_change_pct = st.number_input("Min Δ% (optional)", value=0.0, step=0.5)
        use_min = st.checkbox("Apply Min Δ%", value=False)
        max_change_pct = st.number_input("Max Δ% (optional)", value=0.0, step=0.5)
        use_max = st.checkbox("Apply Max Δ%", value=False)
        run = st.button("Run screener", type="primary")

    symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()]
    exchange_val = exchange.strip() or None
    min_val = float(min_change_pct) if use_min else None
    max_val = float(max_change_pct) if use_max else None

    if not symbols:
        st.warning("Укажите хотя бы один тикер (например: BTC,ETH).")
        return

    if run:
        try:
            with st.spinner("Запрашиваю Coinglass и считаю изменения OI..."):
                rows = _run_async(
                    _screen(
                        symbols=symbols,
                        interval=interval,
                        exchange=exchange_val,
                        endpoint_path=endpoint_path,
                        max_concurrency=max_concurrency,
                        min_change_pct=min_val,
                        max_change_pct=max_val,
                        limit=limit,
                        descending=descending,
                    )
                )
        except CoinglassError as e:
            st.error(f"Coinglass error: {e}")
            return
        except Exception as e:
            st.exception(e)
            return

        st.success(f"Готово. Строк: {len(rows)}")
        st.dataframe(_rows_to_dicts(rows), use_container_width=True)

    st.markdown(
        """
**Переменные окружения**
- `COINGLASS_API_KEY` — ключ Coinglass
- `COINGLASS_API_KEY_HEADER` — имя заголовка (по умолчанию `coinglassSecret`)
        """.strip()
    )


if __name__ == "__main__":
    main()

