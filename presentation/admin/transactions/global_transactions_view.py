from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.admin_service import AdminService

console = Console()


def view_global_transactions_view():
    clear_console()

    with get_db() as db:
        service = AdminService(db)
        txs = service.get_global_transactions(limit=30)

    table = Table(
        title="სისტემის ბოლო ტრანზაქციების ჟურნალი (ბოლო 30)",
        header_style="bold magenta",
        border_style="cyan",
    )
    table.add_column("ID", justify="center", style="dim", width=6)
    table.add_column("მომხმარებელი", style="bold cyan")
    table.add_column("ტიპი", justify="center")
    table.add_column("აქტივი", justify="center")
    table.add_column("რაოდენობა", justify="right")
    table.add_column("ფასი", justify="right")
    table.add_column("ჯამური ღირებულება", justify="right", style="green")
    table.add_column("დრო", justify="center", style="dim")

    for tx in txs:
        tx_type = tx["type"]
        if "BUY" in tx_type or "IN" in tx_type or "CREDIT" in tx_type:
            type_style = f"[green]{tx_type}[/green]"
        elif "SELL" in tx_type or "OUT" in tx_type or "DEBIT" in tx_type:
            type_style = f"[red]{tx_type}[/red]"
        else:
            type_style = f"[yellow]{tx_type}[/yellow]"

        time_str = tx["created_at"].strftime("%Y-%m-%d %H:%M:%S") if tx["created_at"] else "N/A"

        table.add_row(
            str(tx["id"]),
            tx["username"],
            type_style,
            tx["symbol"],
            f"{tx['amount']:,.4f}",
            f"${tx['price']:,.2f}",
            f"${tx['total']:,.2f}",
            time_str,
        )

    console.print(table)
    input("\nდააჭირეთ Enter-ს უკან დასაბრუნებლად...")
