from __future__ import annotations

import asyncio
from typing import Any

import streamlit as st
import pandas as pd

try:
    # When run as a package module.
    from .exchanges_client import ExchangeOIClient, ExchangeError
    from .screener import filter_and_sort, screen_open_interest
except ImportError:  # pragma: no cover
    # When executed by `streamlit run path/to/ui_streamlit.py` (no parent package).
    from coinglass_oi_screener.exchanges_client import ExchangeOIClient, ExchangeError
    from coinglass_oi_screener.screener import filter_and_sort, screen_open_interest


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
    sort_by: str,
):
    client = ExchangeOIClient()
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
            sort_by=sort_by,
            descending=descending,
        )
    finally:
        await client.aclose()


def main() -> None:
    st.set_page_config(page_title="Coinglass OI Screener", layout="wide")

    st.title("Coinglass Open Interest Screener")
    st.caption(
        "6 окон (2×3): выбираем биржу + OI таймфрейм (5m/1h/24h). "
        "Внутри таблица на 3 колонки, сортировка — кликом по заголовкам."
    )

    # Exchanges we support in code. Note: some endpoints may be geo-blocked depending on your location.
    exchanges = ["OKX", "Binance", "Bybit"]
    timeframes = ["5m", "1h", "24h"]
    timeframe_to_interval = {"5m": "5m", "1h": "1h", "24h": "1d"}  # Coinglass чаще использует 1d

    with st.sidebar:
        st.subheader("Общие параметры")
        all_futures = st.checkbox("All futures (scan all futures symbols)", value=True)
        symbols_raw = st.text_input("Symbols (через запятую)", value="BTC,ETH,SOL", disabled=all_futures)
        futures_search = st.text_input("Futures filter (contains)", value="", disabled=not all_futures)
        max_symbols = st.slider(
            "Max symbols to scan (performance)",
            min_value=10,
            max_value=1000,
            value=200,
            step=10,
            disabled=not all_futures,
        )
        st.caption("Источник данных: публичные API бирж (без Coinglass).")
        endpoint_path = st.text_input("Endpoint path (ignored for exchanges)", value="open_interest_history")
        max_concurrency = st.slider("Concurrency", min_value=1, max_value=50, value=10)
        top_n = st.slider("Rows per window", min_value=5, max_value=200, value=30)
        run_all = st.button("Run all windows", type="primary")

    symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()]

    if not all_futures and not symbols:
        st.warning("Укажите хотя бы один тикер (например: BTC,ETH).")
        return

    @st.cache_data(ttl=3600, show_spinner=False)
    def _cached_universe(exchange: str) -> list[str]:
        async def _run():
            c = ExchangeOIClient()
            try:
                return await c.list_futures_symbols(exchange=exchange)
            finally:
                await c.aclose()

        return _run_async(_run())

    @st.cache_data(ttl=60, show_spinner=False)
    def _cached_screen(
        symbols_tuple: tuple[str, ...],
        interval: str,
        exchange: str | None,
        endpoint_path: str,
        max_concurrency: int,
        limit: int,
        descending: bool,
        sort_by: str,
    ) -> list[dict[str, Any]]:
        rows = _run_async(
            _screen(
                symbols=list(symbols_tuple),
                interval=interval,
                exchange=exchange,
                endpoint_path=endpoint_path,
                max_concurrency=max_concurrency,
                min_change_pct=None,
                max_change_pct=None,
                limit=limit,
                descending=descending,
                sort_by=sort_by,
            )
        )
        # Return only 3 columns for each window
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append({"symbol": r.symbol, "oi_change": r.oi_change, "oi_change_pct": r.oi_change_pct})
        return out

    def render_window(tile_id: int) -> None:
        with st.container(border=True):
            st.markdown(f"**Окно {tile_id}**")

            c1, c2, c3 = st.columns(3)
            with c1:
                ex_choice = st.selectbox(
                    "Биржа",
                    options=exchanges + ["Custom..."],
                    key=f"ex_{tile_id}",
                    index=0,
                )
                exchange_val = None
                if ex_choice == "Custom...":
                    exchange_custom = st.text_input("Custom exchange", value="", key=f"ex_custom_{tile_id}")
                    exchange_val = exchange_custom.strip() or None
                else:
                    exchange_val = ex_choice

            with c2:
                tf_choice = st.selectbox("OI таймфрейм", options=timeframes, key=f"tf_{tile_id}", index=1)
                interval_val = timeframe_to_interval[tf_choice]

            with c3:
                sort_choice = st.selectbox("Сортировка", options=["Δ%", "ΔOI"], key=f"sort_{tile_id}", index=0)
                desc = st.checkbox("По убыванию", value=True, key=f"desc_{tile_id}")

            sort_by = "oi_change_pct" if sort_choice == "Δ%" else "oi_change"

            if all_futures:
                try:
                    uni = _cached_universe(exchange_val or "OKX")
                except Exception as e:
                    st.error(f"Failed to list futures symbols: {e}")
                    return
                q = futures_search.strip().upper()
                if q:
                    uni = [s for s in uni if q in s]
                uni = uni[:max_symbols]
                symbols_for_tile = uni
            else:
                symbols_for_tile = symbols

            # If user didn't click "Run all", still show last results if any (cache hit on rerun).
            if run_all:
                try:
                    data = _cached_screen(
                        symbols_tuple=tuple(symbols_for_tile),
                        interval=interval_val,
                        exchange=exchange_val,
                        endpoint_path=endpoint_path,
                        max_concurrency=max_concurrency,
                        limit=top_n,
                        descending=desc,
                        sort_by=sort_by,
                    )
                except ExchangeError as e:
                    st.error(f"Exchange error: {e}")
                    return
                except Exception as e:
                    st.exception(e)
                    return
                st.session_state[f"data_{tile_id}"] = data

            data = st.session_state.get(f"data_{tile_id}")
            if not data:
                st.info("Нажмите **Run all windows** слева, чтобы загрузить данные.")
                return

            df = pd.DataFrame(data)
            # 3 columns exactly:
            df = df.rename(columns={"symbol": "Symbol", "oi_change": "ΔOI", "oi_change_pct": "Δ%"})
            if "Δ%" in df.columns:
                df["Δ%"] = df["Δ%"].round(2)
            if "ΔOI" in df.columns:
                df["ΔOI"] = df["ΔOI"].round(4)
            df = df[["Symbol", "ΔOI", "Δ%"]]
            st.dataframe(df, use_container_width=True, hide_index=True)

    row1 = st.columns(3)
    row2 = st.columns(3)

    with row1[0]:
        render_window(1)
    with row1[1]:
        render_window(2)
    with row1[2]:
        render_window(3)
    with row2[0]:
        render_window(4)
    with row2[1]:
        render_window(5)
    with row2[2]:
        render_window(6)

    st.markdown(
        """
**Переменные окружения**
- (не требуется) — используем публичные API бирж
        """.strip()
    )


if __name__ == "__main__":
    main()

