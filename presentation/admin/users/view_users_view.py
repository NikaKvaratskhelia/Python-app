from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.admin_service import AdminService

console = Console()


def view_all_users_view():
    clear_console()

    with get_db() as db:
        service = AdminService(db)
        users = service.get_all_users()

    table = Table(
        title="სისტემის რეგისტრირებული მომხმარებლები",
        header_style="bold magenta",
        border_style="cyan",
    )
    table.add_column("ID", justify="center", style="dim", width=6)
    table.add_column("მომხმარებელი", style="bold cyan")
    table.add_column("როლი", justify="center")
    table.add_column("USD ბალანსი", justify="right", style="green")
    table.add_column("კრიპტო აქტივები", style="yellow")
    table.add_column("ორდერები", justify="center")
    table.add_column("რეგისტრაცია", justify="center", style="dim")

    for u in users:
        role_style = "[bold red]ADMIN[/bold red]" if u["role"].upper() == "ADMIN" else "[blue]REGULAR[/blue]"
        reg_date = u["created_at"].strftime("%Y-%m-%d %H:%M") if u["created_at"] else "N/A"
        table.add_row(
            str(u["id"]),
            u["username"],
            role_style,
            f"${u['fiat_balance']:,.2f}",
            u["assets_summary"],
            str(u["orders_count"]),
            reg_date,
        )

    console.print(table)
    input("\nდააჭირეთ Enter-ს უკან დასაბრუნებლად...")
