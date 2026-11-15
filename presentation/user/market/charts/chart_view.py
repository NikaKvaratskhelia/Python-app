from rich.console import Console
from rich.panel import Panel
from core.helpers import clear_console
from services.chart_service import ChartService

console = Console()


def run_interactive_chart_view(default_symbol: str = "BTC"):
    symbol = default_symbol.strip().upper()
    current_key = "3"  # default 24h (1h)

    while True:
        clear_console()
        interval, label, limit = ChartService.INTERVAL_MAP.get(
            current_key, ("1h", "24 საათი (1h)", 24)
        )

        data = ChartService.get_chart_data(symbol, interval=interval, limit=limit)
        if not data:
            console.print(f"[red]{symbol}-ისთვის მონაცემების მოძიება ვერ მოხერხდა.[/red]")
            input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
            return

        is_pos = data["is_positive"]
        color = "green" if is_pos else "red"
        arrow = "+" if is_pos else ""
        change_str = f"[{color}]{arrow}{data['price_change_pct']:.2f}% (${data['price_change']:+,.2f})[/{color}]"

        stats_line = (
            f"მიმდინარე: [bold white]${data['close']:,.2f}[/bold white] | "
            f"დინამიკა: {change_str} | "
            f"High: [green]${data['high']:,.2f}[/green] | "
            f"Low: [red]${data['low']:,.2f}[/red]"
        )

        chart_content = "\n".join(data["chart_lines"])
        sparkline_colored = f"[{color}]{data['sparkline']}[/{color}]"

        full_display = (
            f"{stats_line}\n\n"
            f"[{color}]{chart_content}[/{color}]\n\n"
            f"Trend Sparkline: {sparkline_colored}"
        )

        panel = Panel(
            full_display,
            title=f"[bold cyan]{symbol}/USDT ინტერაქტიული ფასის გრაფიკი ({label})[/bold cyan]",
            border_style=color,
            padding=(1, 2),
        )
        console.print(panel)

        console.print("[dim]ნავიგაცია:[/dim]")
        console.print(" [1] 1 საათი (5m)  [2] 6 საათი (15m)  [3] 24 საათი (1h)  [4] 7 დღე (4h)  [5] 30 დღე (1d)")
        console.print(" [s] სხვა სიმბოლო   [r] განახლება       [0] უკან დაბრუნება")

        choice = input("\nაირჩიეთ: ").strip().lower()

        if choice in ("1", "2", "3", "4", "5"):
            current_key = choice
        elif choice == "s":
            new_sym = input("\nშეიყვანეთ ახალი სიმბოლო (მაგ: ETH, SOL, BTC): ").strip().upper()
            if new_sym:
                symbol = new_sym
        elif choice == "r":
            continue
        elif choice in ("0", "q"):
            clear_console()
            break
