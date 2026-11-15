import sys
import select
import io
from decimal import Decimal
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from core.database import get_db
from infrastructure.persistence.models.wallet_model import WalletModel
from services.binance_ws import BinanceWSManager

console = Console()


def show_live_portfolio_analytics(user_id: int):
    console.print(
        "\n[bold cyan]პორტფოლიოს განაწილება & ანალიტიკა (LIVE სტრიმი)[/bold cyan]"
    )
    console.print("[dim]გამოსასვლელად დააჭირეთ [Enter] ან [Ctrl+C]...[/dim]\n")

    def build_display():
        with get_db() as db:
            from services.wallet_service import WalletService
            service = WalletService(db)
            wallet = service.get_or_create_wallet(user_id)

            fiat_balance = Decimal(str(wallet.fiat_balance))
            raw_assets = [
                {
                    "symbol": a.symbol,
                    "amount": Decimal(str(a.amount)),
                    "avg_price": Decimal(str(a.average_buy_price)),
                }
                for a in wallet.assets
                if a.amount > Decimal("0")
            ]

        ws_prices = BinanceWSManager.get_all_prices()

        total_crypto = Decimal("0.00")
        unrealized_pnl = Decimal("0.00")
        items = []

        for a in raw_assets:
            info = ws_prices.get(a["symbol"])
            cur_price = info["price"] if info else a["avg_price"]
            val = a["amount"] * cur_price
            cost = a["amount"] * a["avg_price"]
            pnl = val - cost
            unrealized_pnl += pnl
            total_crypto += val

            items.append(
                {
                    "symbol": a["symbol"],
                    "amount": a["amount"],
                    "price": cur_price,
                    "value": val,
                    "pnl": pnl,
                }
            )

        total_portfolio = fiat_balance + total_crypto

        pnl_color = "green" if unrealized_pnl >= 0 else "red"
        pnl_sign = "+" if unrealized_pnl >= 0 else ""
        pnl_pct = (
            (unrealized_pnl / (total_portfolio - unrealized_pnl) * 100)
            if (total_portfolio - unrealized_pnl) > 0
            else Decimal("0")
        )

        summary_panel = Panel(
            f"[bold]პორტფოლიოს ჯამური ღირებულება:[/bold] [bold cyan]${total_portfolio:,.2f}[/bold cyan]   |   "
            f"[bold]ფიატი:[/bold] [green]${fiat_balance:,.2f}[/green]   |   "
            f"[bold]კრიპტო:[/bold] ${total_crypto:,.2f}\n"
            f"[bold]მიმდინარე ღია PnL:[/bold] [{pnl_color}]{pnl_sign}${unrealized_pnl:,.2f} ({pnl_sign}{pnl_pct:.2f}%)[/{pnl_color}]",
            title="პორტფოლიოს ანალიტიკა (LIVE)",
            border_style="cyan",
        )

        alloc_table = Table(
            title="აქტივების განაწილება (Portfolio Allocation)",
            show_header=True,
            header_style="bold magenta",
        )
        alloc_table.add_column("აქტივი", style="bold cyan")
        alloc_table.add_column("რაოდენობა", justify="right")
        alloc_table.add_column("Live ფასი", justify="right")
        alloc_table.add_column("ღირებულება ($)", justify="right")
        alloc_table.add_column("წილი (%)", justify="right", style="bold yellow")

        if total_portfolio > Decimal("0"):
            fiat_pct = (fiat_balance / total_portfolio) * Decimal("100")
        else:
            fiat_pct = Decimal("100") if fiat_balance > 0 else Decimal("0")
        alloc_table.add_row(
            "USD (ფიატი)", "-", "$1.00", f"${fiat_balance:,.2f}", f"{fiat_pct:.1f}%"
        )

        for it in items:
            pct = (
                (it["value"] / total_portfolio * 100)
                if total_portfolio > 0
                else Decimal("0")
            )
            p_str = (
                f"${it['price']:,.6f}" if it["price"] < 1 else f"${it['price']:,.2f}"
            )
            alloc_table.add_row(
                f"{it['symbol']}/USDT",
                f"{it['amount']}",
                p_str,
                f"${it['value']:,.2f}",
                f"{pct:.1f}%",
            )

        grid = Table.grid(padding=1)
        grid.add_column()
        grid.add_row(summary_panel)
        grid.add_row(alloc_table)
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
    console.print("\n[yellow]ანალიტიკის მონიტორინგი შეჩერდა.[/yellow]")
