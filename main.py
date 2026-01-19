#!/usr/bin/env python3
"""
Coinglass Open Interest Screener - CLI Interface
"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich import box
import time
import sys

from src.screener import OpenInterestScreener, SortBy
from src.config import Config


console = Console()


def create_oi_table(data, title: str = "Open Interest Screener") -> Table:
    """Create a Rich table for OI data display"""
    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold magenta"
    )
    
    # Add columns
    table.add_column("Symbol", style="bold white", justify="left")
    table.add_column("OI (USD)", justify="right", style="green")
    table.add_column("OI 1h %", justify="right")
    table.add_column("OI 4h %", justify="right")
    table.add_column("OI 24h %", justify="right")
    table.add_column("Price", justify="right", style="yellow")
    table.add_column("Price 24h %", justify="right")
    table.add_column("Volume 24h", justify="right", style="blue")
    
    if data.empty:
        table.add_row("No data available", "", "", "", "", "", "", "")
        return table
    
    for _, row in data.iterrows():
        # Format OI change with colors
        oi_1h = format_change(row.get("oi_change_1h", 0))
        oi_4h = format_change(row.get("oi_change_4h", 0))
        oi_24h = format_change(row.get("oi_change_24h", 0))
        price_24h = format_change(row.get("price_change_24h", 0))
        
        # Format values
        oi_usd = format_usd(row.get("oi_value_usd", 0))
        price = format_price(row.get("price", 0))
        volume = format_usd(row.get("volume_24h", 0))
        
        table.add_row(
            str(row.get("symbol", "N/A")),
            oi_usd,
            oi_1h,
            oi_4h,
            oi_24h,
            price,
            price_24h,
            volume
        )
    
    return table


def format_change(value: float) -> Text:
    """Format percentage change with color"""
    if value > 0:
        return Text(f"+{value:.2f}%", style="green")
    elif value < 0:
        return Text(f"{value:.2f}%", style="red")
    else:
        return Text(f"{value:.2f}%", style="dim")


def format_usd(value: float) -> str:
    """Format USD value"""
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.2f}K"
    else:
        return f"${value:.2f}"


def format_price(value: float) -> str:
    """Format price"""
    if value < 0.0001:
        return f"${value:.8f}"
    elif value < 1:
        return f"${value:.6f}"
    elif value < 100:
        return f"${value:.4f}"
    else:
        return f"${value:,.2f}"


@click.group()
@click.option("--api-key", envvar="COINGLASS_API_KEY", help="Coinglass API key")
@click.pass_context
def cli(ctx, api_key):
    """
    Coinglass Open Interest Screener
    
    A powerful tool for screening cryptocurrency derivatives markets
    based on open interest data from Coinglass.
    """
    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key or Config.COINGLASS_API_KEY
    
    if not ctx.obj["api_key"]:
        console.print(Panel(
            "[yellow]Warning:[/yellow] No API key configured.\n"
            "Some features may be limited.\n\n"
            "Set your API key:\n"
            "  export COINGLASS_API_KEY=your_key\n"
            "  or use --api-key option",
            title="API Key Required",
            border_style="yellow"
        ))


@cli.command()
@click.option("--limit", "-l", default=20, help="Number of results to show")
@click.option("--exchange", "-e", help="Filter by exchange (e.g., Binance)")
@click.option("--min-oi", default=1000000, help="Minimum OI in USD")
@click.option("--sort", "-s", 
              type=click.Choice(["oi", "oi_1h", "oi_4h", "oi_24h", "price", "volume"]),
              default="oi", help="Sort by field")
@click.option("--asc/--desc", default=False, help="Sort order (default: descending)")
@click.pass_context
def screen(ctx, limit, exchange, min_oi, sort, asc):
    """
    Screen coins by open interest with custom filters
    """
    console.print("\n[bold cyan]Fetching Open Interest data...[/bold cyan]\n")
    
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    sort_map = {
        "oi": SortBy.OI_VALUE,
        "oi_1h": SortBy.OI_CHANGE_1H,
        "oi_4h": SortBy.OI_CHANGE_4H,
        "oi_24h": SortBy.OI_CHANGE_24H,
        "price": SortBy.PRICE,
        "volume": SortBy.VOLUME_24H
    }
    
    with console.status("[bold green]Loading data..."):
        result = screener.screen(
            sort_by=sort_map.get(sort, SortBy.OI_VALUE),
            ascending=asc,
            limit=limit,
            exchange=exchange,
            min_oi_usd=min_oi
        )
    
    if result.data.empty:
        console.print("[red]No data available. Check your API key and connection.[/red]")
        return
    
    table = create_oi_table(result.data, f"Open Interest Screener - Top {limit}")
    console.print(table)
    
    # Print summary
    console.print(f"\n[dim]Showing {result.filtered_count} of {result.total_count} coins[/dim]")
    if result.filters_applied:
        console.print(f"[dim]Filters: {', '.join(result.filters_applied)}[/dim]")


@cli.command()
@click.option("--timeframe", "-t", type=click.Choice(["1h", "4h", "24h"]), 
              default="24h", help="Timeframe for change")
@click.option("--limit", "-l", default=15, help="Number of results")
@click.option("--min-oi", default=1000000, help="Minimum OI in USD")
@click.pass_context
def gainers(ctx, timeframe, limit, min_oi):
    """
    Show coins with highest OI increase
    """
    console.print(f"\n[bold green]Top OI Gainers ({timeframe})[/bold green]\n")
    
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    with console.status("[bold green]Loading data..."):
        result = screener.get_top_oi_gainers(
            timeframe=timeframe,
            limit=limit,
            min_oi_usd=min_oi
        )
    
    if result.data.empty:
        console.print("[red]No data available.[/red]")
        return
    
    table = create_oi_table(result.data, f"🚀 OI Gainers ({timeframe})")
    console.print(table)


@cli.command()
@click.option("--timeframe", "-t", type=click.Choice(["1h", "4h", "24h"]), 
              default="24h", help="Timeframe for change")
@click.option("--limit", "-l", default=15, help="Number of results")
@click.option("--min-oi", default=1000000, help="Minimum OI in USD")
@click.pass_context
def losers(ctx, timeframe, limit, min_oi):
    """
    Show coins with highest OI decrease
    """
    console.print(f"\n[bold red]Top OI Losers ({timeframe})[/bold red]\n")
    
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    with console.status("[bold green]Loading data..."):
        result = screener.get_top_oi_losers(
            timeframe=timeframe,
            limit=limit,
            min_oi_usd=min_oi
        )
    
    if result.data.empty:
        console.print("[red]No data available.[/red]")
        return
    
    table = create_oi_table(result.data, f"📉 OI Losers ({timeframe})")
    console.print(table)


@cli.command()
@click.option("--limit", "-l", default=15, help="Number of results")
@click.option("--min-oi", default=500000, help="Minimum OI in USD")
@click.option("--threshold", default=5.0, help="Minimum OI change % threshold")
@click.pass_context
def unusual(ctx, limit, min_oi, threshold):
    """
    Show coins with unusual OI activity
    """
    console.print("\n[bold yellow]Unusual OI Activity[/bold yellow]\n")
    
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    with console.status("[bold green]Loading data..."):
        result = screener.get_unusual_activity(
            oi_change_threshold=threshold,
            limit=limit,
            min_oi_usd=min_oi
        )
    
    if result.data.empty:
        console.print("[yellow]No unusual activity detected.[/yellow]")
        return
    
    table = create_oi_table(result.data, f"⚡ Unusual OI Activity (>{threshold}% change)")
    console.print(table)


@cli.command()
@click.option("--limit", "-l", default=15, help="Number of results")
@click.option("--min-oi", default=1000000, help="Minimum OI in USD")
@click.pass_context
def divergence(ctx, limit, min_oi):
    """
    Show coins with OI/Price divergence (potential reversal signals)
    """
    console.print("\n[bold magenta]OI/Price Divergence Signals[/bold magenta]\n")
    
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    with console.status("[bold green]Loading data..."):
        result = screener.get_divergence_signals(
            limit=limit,
            min_oi_usd=min_oi
        )
    
    if result.data.empty:
        console.print("[yellow]No divergence signals found.[/yellow]")
        return
    
    # Create custom table with signal column
    table = Table(
        title="📊 OI/Price Divergence Signals",
        box=box.ROUNDED,
        header_style="bold cyan"
    )
    
    table.add_column("Signal", style="bold")
    table.add_column("Symbol", style="bold white")
    table.add_column("OI (USD)", justify="right", style="green")
    table.add_column("OI 24h %", justify="right")
    table.add_column("Price 24h %", justify="right")
    
    for _, row in result.data.iterrows():
        signal = row.get("signal", "")
        signal_style = "green" if signal == "BULLISH" else "red"
        
        table.add_row(
            Text(f"{'🟢' if signal == 'BULLISH' else '🔴'} {signal}", style=signal_style),
            str(row.get("symbol", "N/A")),
            format_usd(row.get("oi_value_usd", 0)),
            format_change(row.get("oi_change_24h", 0)),
            format_change(row.get("price_change_24h", 0))
        )
    
    console.print(table)
    console.print("\n[dim]BULLISH: Price ↓, OI ↑ | BEARISH: Price ↑, OI ↓[/dim]")


@cli.command()
@click.pass_context
def summary(ctx):
    """
    Show market summary and statistics
    """
    console.print("\n[bold cyan]Market Summary[/bold cyan]\n")
    
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    with console.status("[bold green]Loading market data..."):
        stats = screener.get_summary_stats()
    
    if not stats:
        console.print("[red]Unable to fetch market data.[/red]")
        return
    
    # Create summary panel
    summary_text = f"""
[bold]Total Coins Tracked:[/bold] {stats.get('total_coins', 'N/A')}
[bold]Total Open Interest:[/bold] {format_usd(stats.get('total_oi_usd', 0))}

[bold]Average OI Changes:[/bold]
  • 1 Hour:  {stats.get('avg_oi_change_1h', 0):+.2f}%
  • 4 Hours: {stats.get('avg_oi_change_4h', 0):+.2f}%
  • 24 Hours: {stats.get('avg_oi_change_24h', 0):+.2f}%

[bold]Market Sentiment:[/bold]
  • Rising OI:  {stats.get('coins_with_rising_oi', 0)} coins
  • Falling OI: {stats.get('coins_with_falling_oi', 0)} coins

[bold]Notable:[/bold]
  • Top OI: {stats.get('top_oi_coin', 'N/A')}
  • Biggest Gainer: {stats.get('biggest_oi_gainer', 'N/A')}
  • Biggest Loser: {stats.get('biggest_oi_loser', 'N/A')}
"""
    
    console.print(Panel(summary_text, title="📈 Market Overview", border_style="cyan"))


@cli.command()
@click.option("--interval", "-i", default=60, help="Refresh interval in seconds")
@click.option("--limit", "-l", default=15, help="Number of results")
@click.pass_context
def watch(ctx, interval, limit):
    """
    Watch OI changes in real-time (auto-refresh)
    """
    console.print(f"\n[bold cyan]Watching OI changes (refresh every {interval}s)[/bold cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    try:
        while True:
            console.clear()
            console.print(f"[bold cyan]Open Interest Screener[/bold cyan] - Last update: {time.strftime('%H:%M:%S')}\n")
            
            result = screener.screen(
                sort_by=SortBy.OI_CHANGE_1H,
                limit=limit,
                min_oi_usd=1_000_000
            )
            
            if not result.data.empty:
                table = create_oi_table(result.data, "Live OI Monitor")
                console.print(table)
            else:
                console.print("[red]No data available[/red]")
            
            console.print(f"\n[dim]Next refresh in {interval} seconds... (Ctrl+C to stop)[/dim]")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped watching.[/yellow]")


@cli.command()
@click.argument("symbol")
@click.pass_context
def info(ctx, symbol):
    """
    Show detailed info for a specific coin
    """
    console.print(f"\n[bold cyan]Coin Info: {symbol.upper()}[/bold cyan]\n")
    
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    with console.status(f"[bold green]Fetching {symbol.upper()} data..."):
        result = screener.screen(limit=500, min_oi_usd=0)
    
    if result.data.empty:
        console.print("[red]No data available.[/red]")
        return
    
    # Find the coin
    coin_data = result.data[result.data["symbol"].str.upper() == symbol.upper()]
    
    if coin_data.empty:
        console.print(f"[red]Coin {symbol.upper()} not found in OI data.[/red]")
        return
    
    row = coin_data.iloc[0]
    
    info_text = f"""
[bold]Symbol:[/bold] {row.get('symbol', 'N/A')}
[bold]Exchange:[/bold] {row.get('exchange', 'Aggregated')}

[bold cyan]Open Interest:[/bold cyan]
  • Value (USD): {format_usd(row.get('oi_value_usd', 0))}
  • Change 1h:   {row.get('oi_change_1h', 0):+.2f}%
  • Change 4h:   {row.get('oi_change_4h', 0):+.2f}%
  • Change 24h:  {row.get('oi_change_24h', 0):+.2f}%

[bold yellow]Price:[/bold yellow]
  • Current:    {format_price(row.get('price', 0))}
  • Change 24h: {row.get('price_change_24h', 0):+.2f}%

[bold blue]Volume:[/bold blue]
  • 24h Volume: {format_usd(row.get('volume_24h', 0))}
  • OI/Volume:  {row.get('oi_volume_ratio', 0):.2f}

[bold magenta]Additional:[/bold magenta]
  • Market Cap:       {format_usd(row.get('market_cap', 0))}
  • Avg Funding Rate: {row.get('avg_funding_rate', 0):.4f}%
"""
    
    console.print(Panel(info_text, title=f"📊 {symbol.upper()} Details", border_style="cyan"))


@cli.command()
@click.option("--format", "-f", type=click.Choice(["table", "csv", "json"]), 
              default="csv", help="Export format")
@click.option("--output", "-o", help="Output file path")
@click.option("--limit", "-l", default=100, help="Number of results")
@click.pass_context
def export(ctx, format, output, limit):
    """
    Export OI data to file
    """
    screener = OpenInterestScreener(ctx.obj.get("api_key"))
    
    with console.status("[bold green]Fetching data for export..."):
        result = screener.screen(limit=limit, min_oi_usd=100000)
    
    if result.data.empty:
        console.print("[red]No data to export.[/red]")
        return
    
    formatted = screener.format_results(result, format_type=format)
    
    if output:
        with open(output, "w") as f:
            f.write(formatted)
        console.print(f"[green]Data exported to {output}[/green]")
    else:
        console.print(formatted)


@cli.command()
def exchanges():
    """
    List supported exchanges
    """
    console.print("\n[bold cyan]Supported Exchanges[/bold cyan]\n")
    
    table = Table(box=box.SIMPLE)
    table.add_column("Exchange", style="bold")
    table.add_column("Status", style="green")
    
    for ex in Config.SUPPORTED_EXCHANGES:
        table.add_row(ex, "✓ Available")
    
    console.print(table)


if __name__ == "__main__":
    cli()
