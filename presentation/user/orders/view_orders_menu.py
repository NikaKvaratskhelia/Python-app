import sys
import select
import io
from decimal import Decimal
from rich.console import Console
from rich.live import Live
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from infrastructure.persistence.models.order_model import OrderModel
from infrastructure.persistence.models.wallet_model import WalletModel
from services.binance_ws import BinanceWSManager

console = Console()


def run_view_orders_menu(user_id: int):
    clear_console()

    print("\nაირჩიეთ ფილტრი:")

    print("1. ყველა (ALL)")
    print("2. მხოლოდ მიმდინარე (PENDING)")
    print("3. შესრულებული (EXECUTED)")
    print("4. გაუქმებული (CANCELLED)")
    print("0. უკან დაბრუნება")

    f_choice = input("აირჩიეთ (1-4, default 1): ").strip()
    if f_choice == "0":
        clear_console()
        return

    filter_map = {
        "1": None,
        "2": "PENDING",
        "3": "EXECUTED",
        "4": "CANCELLED",
    }
    status_filter = filter_map.get(f_choice, None)
    title_suffix = f" [{status_filter}]" if status_filter else " [ყველა]"

    console.print(
        f"\n[bold cyan]ორდერების სია{title_suffix} (LIVE განახლება)[/bold cyan]"
    )
    console.print("[dim]გამოსასვლელად დააჭირეთ [Enter] ან [Ctrl+C]...[/dim]\n")

    def build_table() -> Table:
        with get_db() as db:
            wallet = (
                db.query(WalletModel).filter(WalletModel.user_id == user_id).first()
            )
            if not wallet:
                orders = []
            else:
                q = db.query(OrderModel).filter(OrderModel.wallet_id == wallet.id)
                if status_filter:
                    q = q.filter(OrderModel.status == status_filter)
                raw_orders = q.order_by(OrderModel.id.desc()).all()
                orders = [
                    {
                        "id": o.id,
                        "type": o.order_type,
                        "symbol": o.symbol,
                        "amount": Decimal(str(o.amount)),
                        "target_price": Decimal(str(o.target_price)),
                        "status": o.status,
                    }
                    for o in raw_orders
                ]

        ws_prices = BinanceWSManager.get_all_prices()

        table = Table(
            title=f"ორდერები{title_suffix} (LIVE ბაზრის ფასებით)",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("ID", justify="right", width=4)
        table.add_column("ტიპი")
        table.add_column("სიმბოლო")
        table.add_column("რაოდენობა", justify="right")
        table.add_column("სამიზნე ფასი", justify="right")
        table.add_column("Live ფასი", justify="right")
        table.add_column("სტატუსი", justify="center")

        if not orders:
            table.add_row("-", "ორდერები არ მოიძებნა", "-", "-", "-", "-", "-")
            return table

        for o in orders:
            type_color = (
                "green"
                if o["type"] == "BUY_LIMIT"
                else "yellow" if o["type"] == "SELL_LIMIT" else "red"
            )
            status_color = (
                "yellow"
                if o["status"] == "PENDING"
                else "green" if o["status"] == "EXECUTED" else "dim"
            )

            sym_info = ws_prices.get(o["symbol"])
            cur_price = sym_info["price"] if sym_info else None
            cur_price_str = f"${cur_price:,.2f}" if cur_price else "-"

            table.add_row(
                str(o["id"]),
                f"[{type_color}]{o['type']}[/{type_color}]",
                f"{o['symbol']}/USDT",
                f"{o['amount']}",
                f"${o['target_price']:,.2f}",
                cur_price_str,
                f"[{status_color}]{o['status']}[/{status_color}]",
            )

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
    console.print("\n[yellow]ორდერების მონიტორინგი შეჩერდა.[/yellow]")
