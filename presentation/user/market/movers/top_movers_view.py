import sys
import select
import io
from rich.console import Console
from rich.live import Live
from rich.table import Table
from services.binance_ws import BinanceWSManager

console = Console()


def show_live_top_movers(limit: int = 5):
    console.print("\n[bold cyan]დღის ტოპ ზრდა / ვარდნა (LIVE ბაზრის სტრიმი)[/bold cyan]")
    console.print("[dim]გამოსასვლელად დააჭირეთ [Enter] ან [Ctrl+C]...[/dim]\n")

    def build_display():
        ws_prices = BinanceWSManager.get_all_prices()
        if not ws_prices:
            return Table(title="[dim]იტვირთება საბაზრო მონაცემები...[/dim]")

        # Filter and sort
        items = [
            {
                "symbol": sym,
                "price": data["price"],
                "change": data.get("change", 0),
            }
            for sym, data in ws_prices.items()
            if data.get("price", 0) > 0
        ]
        sorted_items = sorted(items, key=lambda x: x["change"], reverse=True)

        gainers = sorted_items[:limit]
        losers = sorted_items[-limit:][::-1]

        gainers_table = Table(
            title="TOP 5 მზარდი მონეტა (LIVE Gainers)",
            show_header=True,
            header_style="bold green",
        )
        gainers_table.add_column("სიმბოლო", style="bold cyan")
        gainers_table.add_column("ფასი ($)", justify="right")
        gainers_table.add_column(
            "24სთ ცვლილება", justify="right", style="bold green"
        )

        for g in gainers:
            p_str = (
                f"${g['price']:,.6f}" if g["price"] < 1 else f"${g['price']:,.2f}"
            )
            sign = "+" if g["change"] >= 0 else ""
            gainers_table.add_row(f"{g['symbol']}/USDT", p_str, f"{sign}{g['change']:.2f}%")

        losers_table = Table(
            title="TOP 5 დაცემული მონეტა (LIVE Losers)",
            show_header=True,
            header_style="bold red",
        )
        losers_table.add_column("სიმბოლო", style="bold cyan")
        losers_table.add_column("ფასი ($)", justify="right")
        losers_table.add_column(
            "24სთ ცვლილება", justify="right", style="bold red"
        )

        for l in losers:
            p_str = (
                f"${l['price']:,.6f}" if l["price"] < 1 else f"${l['price']:,.2f}"
            )
            sign = "+" if l["change"] >= 0 else ""
            losers_table.add_row(f"{l['symbol']}/USDT", p_str, f"{sign}{l['change']:.2f}%")

        grid = Table.grid(padding=1)
        grid.add_column()
        grid.add_row(gainers_table)
        grid.add_row(losers_table)
        return grid

    try:
        with Live(build_display(), refresh_per_second=2, console=console) as live:
            while True:
                live.update(build_display())
                try:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.5)
                except (io.UnsupportedOperation, ValueError, OSError):
                    rlist = [sys.stdin]
                if rlist:
                    sys.stdin.readline()
                    break
    except KeyboardInterrupt:
        pass
    clear_console()
    console.print("\n[yellow]ტოპ ლიდერების მონიტორინგი შეჩერდა.[/yellow]")
