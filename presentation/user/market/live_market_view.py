import sys
import select
import io
from decimal import Decimal
from typing import Optional, List
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from services.binance_ws import BinanceWSManager
from services.market_service import MarketService

console = Console()

DEFAULT_WATCH = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP", "ADA", "AVAX", "DOT", "LINK"]


def run_live_market_view(
    symbols: Optional[List[str]] = None,
    title: str = "LIVE კრიპტო ფასები (WebSocket Stream)",
):
    watch_symbols = symbols if symbols else DEFAULT_WATCH
    prev_prices = {}

    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("[dim]გამოსასვლელად დააჭირეთ [Enter] ან [Ctrl+C]...[/dim]\n")

    def build_table() -> Table:
        table = Table(
            title=title,
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("სიმბოლო", style="bold cyan")
        table.add_column("მიმდინარე ფასი ($)", justify="right", style="bold white")
        table.add_column("24სთ მაქს ($)", justify="right", style="dim")
        table.add_column("24სთ მინ ($)", justify="right", style="dim")
        table.add_column("დინამიკა", justify="center")

        all_data = BinanceWSManager.get_all_prices()

        for sym in watch_symbols:
            item = all_data.get(sym)
            if not item:
                table.add_row(f"{sym}/USDT", "[dim]იტვირთება...[/dim]", "-", "-", "-")
                continue

            cur_price = item["price"]
            prev_price = prev_prices.get(sym, cur_price)

            if cur_price > prev_price:
                tick_icon = "[green]+ UP[/green]"
            elif cur_price < prev_price:
                tick_icon = "[red]- DOWN[/red]"
            else:
                tick_icon = "[dim]= FLAT[/dim]"

            prev_prices[sym] = cur_price

            cur_str = f"${cur_price:,.6f}" if cur_price < 1 else f"${cur_price:,.2f}"
            high_str = (
                f"${item['high']:,.2f}"
                if item["high"] >= 1
                else f"${item['high']:,.6f}"
            )
            low_str = (
                f"${item['low']:,.2f}"
                if item["low"] >= 1
                else f"${item['low']:,.6f}"
            )

            table.add_row(f"{sym}/USDT", cur_str, high_str, low_str, tick_icon)

        return table

    try:
        with Live(build_table(), refresh_per_second=2, console=console) as live:
            while True:
                live.update(build_table())
                try:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.5)
                except (io.UnsupportedOperation, ValueError, OSError):
                    rlist = [sys.stdin]
                if rlist:
                    sys.stdin.readline()
                    break
    except KeyboardInterrupt:
        pass
    console.print("\n[yellow]LIVE სტრიმი შეჩერდა.[/yellow]")


def run_live_asset_preview(
    symbol: str, action_title: str = "ყიდვა"
) -> Optional[Decimal]:
    sym = symbol.strip().upper()
    if sym.endswith("USDT"):
        sym = sym[:-4]

    stats = MarketService.get_market_stats(sym)
    if not stats:
        console.print(f"[red]სიმბოლო '{sym}' ვერ მოიძებნა ბაზარზე.[/red]")
        return None

    prev_price = stats["price"]
    tick_str = "[dim]= FLAT[/dim]"
    last_known_price = stats["price"]

    def build_panel(cur_price: Decimal, t_icon: str, current_stats: dict) -> Panel:
        price_str = f"${cur_price:,.6f}" if cur_price < 1 else f"${cur_price:,.2f}"
        high = current_stats.get("high")
        low = current_stats.get("low")
        vol = current_stats.get("volume")
        high_str = f"${high:,.2f}" if high else "-"
        low_str = f"${low:,.2f}" if low else "-"
        vol_str = f"{vol:,.2f}" if vol else "-"

        change = current_stats.get("price_change_percent", Decimal("0"))
        c_sign = "+" if change >= 0 else ""
        c_color = "green" if change >= 0 else "red"
        change_str = f"[{c_color}]{c_sign}{change:.2f}%[/{c_color}]"

        content = (
            f"[bold]სიმბოლო:[/bold] [bold cyan]{sym}/USDT[/bold cyan]   |   "
            f"[bold]24სთ ცვლილება:[/bold] {change_str}\n\n"
            f"[bold]მიმდინარე LIVE ფასი:[/bold] [bold white underline]{price_str}[/bold white underline]  {t_icon}\n\n"
            f"[dim]24სთ მაქს:[/dim] {high_str}   |   [dim]24სთ მინ:[/dim] {low_str}   |   [dim]მოცულობა:[/dim] {vol_str}\n\n"
            f"[bold green]დააჭირეთ [Enter] {action_title}-ზე გადასასვლელად[/bold green]  [dim]ან [0 / q] გაუქმება[/dim]"
        )
        return Panel(
            content,
            title=f"LIVE ფასის პრევიუ: {sym}/USDT",
            border_style="cyan",
        )

    try:
        with Live(
            build_panel(last_known_price, tick_str, stats),
            refresh_per_second=4,
            console=console,
        ) as live:
            while True:
                new_stats = MarketService.get_market_stats(sym) or stats
                cur_price = new_stats["price"]
                last_known_price = cur_price

                if cur_price > prev_price:
                    tick_str = "[bold green]+ UP[/bold green]"
                elif cur_price < prev_price:
                    tick_str = "[bold red]- DOWN[/bold red]"
                else:
                    tick_str = "[dim]= FLAT[/dim]"

                prev_price = cur_price
                live.update(build_panel(cur_price, tick_str, new_stats))

                try:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.3)
                except (io.UnsupportedOperation, ValueError, OSError):
                    rlist = [sys.stdin]
                if rlist:
                    line = sys.stdin.readline().strip().lower()
                    if line in ("0", "q"):
                        console.print(f"\n[yellow]{action_title} გაუქმდა.[/yellow]")
                        return None
                    return cur_price
    except KeyboardInterrupt:
        console.print(f"\n[yellow]{action_title} გაუქმდა.[/yellow]")
        return None
