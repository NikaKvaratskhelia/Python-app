import sys
import select
import io
from decimal import Decimal
from rich.console import Console
from rich.live import Live
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.alert_service import AlertService
from services.binance_ws import BinanceWSManager
from presentation.user.market.alerts.create_alert_menu import run_create_alert_menu
from presentation.user.market.alerts.delete_alert_menu import run_delete_alert_menu

console = Console()


def alerts_menu(user_id: int):
    clear_console()

    def show_live_alerts_stream():
        console.print("\n[bold cyan]ფასის შეტყობინებები (LIVE სტრიმი & მონიტორინგი)[/bold cyan]")
        console.print("[dim]მენიუზე გადასასვლელად დააჭირეთ [Enter] ან [Ctrl+C]...[/dim]\n")

        def build_table() -> Table:
            with get_db() as db:
                alert_svc = AlertService(db)
                raw_alerts = alert_svc.get_user_alerts(user_id, active_only=False)
                alerts = [
                    {
                        "id": a.id,
                        "symbol": a.symbol,
                        "condition": a.condition,
                        "target_price": Decimal(str(a.target_price)),
                        "is_triggered": a.is_triggered,
                    }
                    for a in raw_alerts
                ]

            ws_prices = BinanceWSManager.get_all_prices()

            table = Table(
                title="თქვენი შეტყობინებები (LIVE ბაზრის ფასებით)",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("ID", justify="right", width=4)
            table.add_column("სიმბოლო", style="bold cyan")
            table.add_column("პირობა")
            table.add_column("სამიზნე ფასი ($)", justify="right")
            table.add_column("Live ფასი ($)", justify="right")
            table.add_column("სტატუსი", justify="center")

            if not alerts:
                table.add_row("-", "შეტყობინებები არ არის დაყენებული", "-", "-", "-", "-")
                return table

            for a in alerts:
                status_str = (
                    "[green]TRIGGERED[/green]"
                    if a["is_triggered"]
                    else "[yellow]ACTIVE[/yellow]"
                )
                info = ws_prices.get(a["symbol"])
                cur_price = info["price"] if info else None
                cur_str = f"${cur_price:,.2f}" if cur_price else "-"

                table.add_row(
                    str(a["id"]),
                    f"{a['symbol']}/USDT",
                    f"როცა ფასი {a['condition']}",
                    f"${a['target_price']:,.2f}",
                    cur_str,
                    status_str,
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

    # First show live alerts stream
    show_live_alerts_stream()

    while True:
        print("\n--- შეტყობინებების მართვა ---")
        print("1. შეტყობინებების LIVE სტრიმი")
        print("2. ახალი შეტყობინების დამატება")
        print("3. შეტყობინების წაშლა")
        print("0. უკან დაბრუნება")

        a_choice = input("\nაირჩიეთ (1/2/3/0): ").strip()
        if a_choice == "1":
            clear_console()
            show_live_alerts_stream()
        elif a_choice == "2":
            run_create_alert_menu(user_id)
        elif a_choice == "3":
            run_delete_alert_menu(user_id)
        elif a_choice == "0":
            clear_console()
            break
        else:
            clear_console()
            print("არასწორი არჩევანი.")
