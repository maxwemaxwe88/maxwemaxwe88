from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from importlib.resources import files
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .coinglass_client import CoinglassClient, CoinglassError
from .screener import filter_and_sort, screen_open_interest


app = typer.Typer(add_completion=False, help="Coinglass Open Interest screener (CLI).")
console = Console()


def _render_table(rows) -> None:
    t = Table(title="Open Interest Screener", show_lines=False)
    t.add_column("Symbol", style="bold")
    t.add_column("OI latest", justify="right")
    t.add_column("OI prev", justify="right")
    t.add_column("Δ OI", justify="right")
    t.add_column("Δ %", justify="right")
    t.add_column("t(latest)", justify="right")
    t.add_column("t(prev)", justify="right")

    for r in rows:
        t.add_row(
            r.symbol,
            "" if r.oi_latest is None else f"{r.oi_latest:,.4f}",
            "" if r.oi_prev is None else f"{r.oi_prev:,.4f}",
            "" if r.oi_change is None else f"{r.oi_change:,.4f}",
            "" if r.oi_change_pct is None else f"{r.oi_change_pct:,.2f}%",
            "" if r.t_latest is None else str(r.t_latest),
            "" if r.t_prev is None else str(r.t_prev),
        )
    console.print(t)


@app.command("screen")
def screen(
    symbols: str = typer.Option(..., help="Comma-separated symbols, e.g. BTC,ETH,SOL"),
    interval: str = typer.Option("1h", help="Interval for history points (depends on Coinglass)"),
    exchange: Optional[str] = typer.Option(None, help="Optional exchange, e.g. Binance"),
    min_change_pct: Optional[float] = typer.Option(None, help="Min OI change % filter"),
    max_change_pct: Optional[float] = typer.Option(None, help="Max OI change % filter"),
    limit: int = typer.Option(50, help="Limit rows after sorting"),
    endpoint_path: str = typer.Option("open_interest_history", help="Override Coinglass endpoint path"),
    max_concurrency: int = typer.Option(10, help="Max concurrent API calls"),
) -> None:
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        raise typer.BadParameter("No symbols provided")

    async def _run():
        client = CoinglassClient()
        try:
            rows = await screen_open_interest(
                client,
                symbols=sym_list,
                interval=interval,
                exchange=exchange,
                endpoint_path=endpoint_path,
                max_concurrency=max_concurrency,
            )
            rows2 = filter_and_sort(
                rows,
                min_change_pct=min_change_pct,
                max_change_pct=max_change_pct,
                limit=limit,
            )
            _render_table(rows2)
        finally:
            await client.aclose()

    try:
        asyncio.run(_run())
    except CoinglassError as e:
        console.print(f"[red]Coinglass error:[/red] {e}")
        raise typer.Exit(code=2)


@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
) -> None:
    """
    Run HTTP API server (FastAPI).
    """
    import uvicorn

    uvicorn.run("coinglass_oi_screener.api:app", host=host, port=port, reload=False)


@app.command("ui")
def ui(
    host: str = typer.Option("0.0.0.0", help="Bind host for Streamlit"),
    port: int = typer.Option(8501, help="Bind port for Streamlit"),
) -> None:
    """
    Run Streamlit UI (visual client).
    """
    # `python -m streamlit` is portable (Windows/macOS/Linux).
    # Use current interpreter to avoid `python3`/`py` mismatches on Windows.
    ui_path = files("coinglass_oi_screener").joinpath("ui_streamlit.py")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_path),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]
    raise typer.Exit(code=subprocess.call(cmd))

