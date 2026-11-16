from decimal import Decimal
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from core.database import get_db
from core.helpers import clear_console, run_live_loop
from infrastructure.persistence.models.order_model import OrderModel
from infrastructure.persistence.models.transaction_model import TransactionModel
from services.wallet_service import WalletService
from services.binance_ws import BinanceWSManager

console = Console()


def run_live_wallet_view(user_id: int, username: str):
    console.print(
        f"\n[bold green]რეალურ დროში საფულისა და ბოტის სტრიმი ({username})[/bold green]"
    )
    console.print("[dim]გამოსასვლელად დააჭირეთ [Enter] ან [Ctrl+C]...[/dim]\n")

    def build_display():
        with get_db() as db:
            service = WalletService(db)
            wallet = service.get_or_create_wallet(user_id)
            fiat_balance = Decimal(str(wallet.fiat_balance))
            wallet_id = wallet.id

            raw_assets = [
                {
                    "symbol": asset.symbol,
                    "amount": Decimal(str(asset.amount)),
                    "avg_price": Decimal(str(asset.average_buy_price)),
                }
                for asset in wallet.assets
                if asset.amount > Decimal("0")
            ]

            pending_query = (
                db.query(OrderModel)
                .filter(
                    OrderModel.wallet_id == wallet_id, OrderModel.status == "PENDING"
                )
                .all()
            )
            raw_orders = [
                {
                    "id": o.id,
                    "order_type": str(o.order_type),
                    "symbol": str(o.symbol),
                    "amount": Decimal(str(o.amount)),
                    "target_price": Decimal(str(o.target_price)),
                }
                for o in pending_query
            ]

            tx_query = (
                db.query(TransactionModel)
                .filter(TransactionModel.wallet_id == wallet_id)
                .order_by(TransactionModel.id.desc())
                .limit(4)
                .all()
            )
            raw_txs = [
                {
                    "type": str(t.type),
                    "symbol": str(t.symbol or "USD"),
                    "amount": Decimal(str(t.amount)),
                    "price": Decimal(str(t.price)) if t.price else None,
                    "time": (
                        t.created_at.strftime("%H:%M:%S")
                        if hasattr(t.created_at, "strftime")
                        else str(t.created_at)
                    ),
                }
                for t in tx_query
            ]

        ws_prices = BinanceWSManager.get_all_prices()
        total_crypto = Decimal("0.00")
        assets_rows = []

        for asset in raw_assets:
            info = ws_prices.get(asset["symbol"])
            price = info["price"] if info else asset["avg_price"]
            val = asset["amount"] * price
            total_crypto += val

            pnl_usd = val - (asset["amount"] * asset["avg_price"])
            pnl_pct = (
                ((price - asset["avg_price"]) / asset["avg_price"] * 100)
                if asset["avg_price"] > 0
                else Decimal("0")
            )
            pnl_sign = "+" if pnl_usd >= 0 else ""
            color = "green" if pnl_usd >= 0 else "red"

            price_str = f"${price:,.6f}" if price < 1 else f"${price:,.2f}"
            avg_str = (
                f"${asset['avg_price']:,.6f}"
                if asset["avg_price"] < 1
                else f"${asset['avg_price']:,.2f}"
            )
            val_str = f"${val:,.2f}"
            pnl_str = f"[{color}]{pnl_sign}${pnl_usd:,.2f} ({pnl_sign}{pnl_pct:.2f}%)[/{color}]"

            assets_rows.append(
                (
                    asset["symbol"],
                    f"{asset['amount']}",
                    price_str,
                    val_str,
                    avg_str,
                    pnl_str,
                )
            )

        total_portfolio = fiat_balance + total_crypto

        assets_table = Table(
            title="აქტივები (Live ფასებით)",
            show_header=True,
            header_style="bold magenta",
        )
        assets_table.add_column("აქტივი", style="bold cyan")
        assets_table.add_column("რაოდენობა", justify="right")
        assets_table.add_column("Live ფასი", justify="right")
        assets_table.add_column("ღირებულება", justify="right")
        assets_table.add_column("საშ. ფასი", justify="right")
        assets_table.add_column("PnL", justify="right")

        if not assets_rows:
            assets_table.add_row("-", "აქტივები არ გაქვთ", "-", "-", "-", "-")
        else:
            for r in assets_rows:
                assets_table.add_row(*r)

        orders_table = Table(
            title="ბოტის აქტიური ორდერები (PENDING)",
            show_header=True,
            header_style="bold cyan",
        )
        orders_table.add_column("ID", justify="right", width=4)
        orders_table.add_column("ტიპი")
        orders_table.add_column("სიმბოლო")
        orders_table.add_column("რაოდენობა", justify="right")
        orders_table.add_column("სამიზნე ფასი", justify="right")

        if not raw_orders:
            orders_table.add_row("-", "აქტიური ორდერები არ არის", "-", "-", "-")
        else:
            for o in raw_orders:
                type_color = (
                    "green"
                    if o["order_type"] == "BUY_LIMIT"
                    else "yellow" if o["order_type"] == "SELL_LIMIT" else "red"
                )
                orders_table.add_row(
                    str(o["id"]),
                    f"[{type_color}]{o['order_type']}[/{type_color}]",
                    f"{o['symbol']}/USDT",
                    f"{o['amount']}",
                    f"${o['target_price']:,.2f}",
                )

        tx_table = Table(
            title="ბოლო ტრანზაქციები", show_header=True, header_style="bold yellow"
        )
        tx_table.add_column("თარიღი", style="dim")
        tx_table.add_column("ტიპი")
        tx_table.add_column("აქტივი")
        tx_table.add_column("რაოდენობა", justify="right")
        tx_table.add_column("ფასი", justify="right")

        if not raw_txs:
            tx_table.add_row("-", "ტრანზაქციები არ არის", "-", "-", "-")
        else:
            for tx in raw_txs:
                t_color = (
                    "green"
                    if tx["type"] in ("BUY", "DEPOSIT", "TRANSFER_IN")
                    else "yellow" if tx["type"] == "SELL" else "red"
                )
                price_str = f"${tx['price']:,.2f}" if tx["price"] is not None else "-"
                tx_table.add_row(
                    tx["time"],
                    f"[{t_color}]{tx['type']}[/{t_color}]",
                    tx["symbol"],
                    f"{tx['amount']}",
                    price_str,
                )

        summary_panel = Panel(
            f"[bold]ფიატ ბალანსი:[/bold] [green]${fiat_balance:,.2f}[/green]   |   "
            f"[bold]კრიპტო ღირებულება:[/bold] ${total_crypto:,.2f}   |   "
            f"[bold cyan]პორტფოლიოს ჯამური ღირებულება:[/bold cyan] [bold underline]${total_portfolio:,.2f}[/bold underline]",
            title=f"საფულე: {username}",
            border_style="green",
        )

        grid = Table.grid(padding=1)
        grid.add_column()
        grid.add_row(summary_panel)
        grid.add_row(assets_table)
        grid.add_row(orders_table)
        grid.add_row(tx_table)

        return grid

    run_live_loop(build_display, console=console)
    console.print("\n[yellow]LIVE საფულის მონიტორინგი შეჩერდა.[/yellow]")
