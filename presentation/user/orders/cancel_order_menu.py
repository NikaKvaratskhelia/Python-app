from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from services.order_service import OrderService

console = Console()


def run_cancel_order_menu(user_id: int):
    clear_console()
    with get_db() as db:
        order_svc = OrderService(db)

        pending_orders = order_svc.get_orders(user_id, status_filter="PENDING")

        if not pending_orders:
            console.print("\n[yellow]აქტიური (PENDING) ორდერები არ გაქვთ.[/yellow]")
            input("\nდააჭირეთ Enter-ს უკან დასაბრუნებლად...")
            clear_console()
            return

        table = Table(
            title="გასაუქმებელი ორდერები (PENDING)",
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("ID", justify="right", width=4)
        table.add_column("ტიპი")
        table.add_column("სიმბოლო")
        table.add_column("რაოდენობა", justify="right")
        table.add_column("სამიზნე ფასი", justify="right")

        for ord in pending_orders:
            type_color = (
                "green"
                if ord.order_type == "BUY_LIMIT"
                else "yellow" if ord.order_type == "SELL_LIMIT" else "red"
            )

            table.add_row(
                str(ord.id),
                f"[{type_color}]{ord.order_type}[/{type_color}]",
                f"{ord.symbol}/USDT",
                f"{ord.amount}",
                f"${ord.target_price:,.2f}",
            )

        console.print(table)

        cancel_id_str = input(
            "\nშეიყვანეთ გასაუქმებელი ორდერის ID (ან 0 უკან გამოსასვლელად): "
        ).strip()

        if cancel_id_str in ("0", ""):
            return

        parse_id = Result.try_catch(
            lambda: int(cancel_id_str),
            lambda _: "ID უნდა იყოს მთელი რიცხვი.",
        )

        if parse_id.is_failure:
            console.print(f"[red]შეცდომა: {parse_id.error}[/red]")
            return

        cancel_res = order_svc.cancel_order(parse_id.value, user_id)

        if cancel_res.is_success:
            ord = cancel_res.value
            console.print(
                f"\n[green]ორდერი #{ord.id} ({ord.symbol} {ord.order_type}) წარმატებით გაუქმდა![/green]"
            )
            console.print("[dim]დარეზერვებული თანხა/აქტივი დაგიბრუნდათ საფულეში.[/dim]")
        else:
            console.print(f"\n[red]შეცდომა: {cancel_res.error}[/red]")

        input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
        clear_console()
