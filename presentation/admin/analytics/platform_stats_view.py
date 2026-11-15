from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.admin_service import AdminService

console = Console()


def view_platform_stats_view():
    clear_console()

    with get_db() as db:
        service = AdminService(db)
        stats = service.get_platform_stats()

    table = Table.grid(padding=(0, 2))
    table.add_column("მეტრიკა", style="bold cyan")
    table.add_column("მნიშვნელობა", style="bold green", justify="right")

    table.add_row("სულ რეგისტრირებული მომხმარებელი:", str(stats["total_users"]))
    table.add_row(
        "სისტემის Fiat ლიკვიდურობა (USD):",
        f"${stats['total_fiat_liquidity']:,.2f}",
    )
    table.add_row(
        "განხორციელებული ტრანზაქციები:", str(stats["total_transactions"])
    )
    table.add_row(
        "პლატფორმის შემოსავალი (Trading Fees):",
        f"${stats['total_fees_collected']:,.2f}",
    )
    table.add_row(
        "აქტიური (PENDING) ორდერები:", str(stats["pending_orders"])
    )
    table.add_row(
        "შესრულებული (EXECUTED) ორდერები:", str(stats["executed_orders"])
    )
    table.add_row(
        "გაუქმებული (CANCELLED) ორდერები:", str(stats["cancelled_orders"])
    )
    table.add_row(
        "აქტიური ფასის შეტყობინებები (Alerts):", str(stats["active_alerts"])
    )

    panel = Panel(
        table,
        title="[bold yellow]პლატფორმის გლობალური სტატისტიკა[/bold yellow]",
        border_style="magenta",
        padding=(1, 2),
    )

    console.print(panel)
    input("\nდააჭირეთ Enter-ს უკან დასაბრუნებლად...")
