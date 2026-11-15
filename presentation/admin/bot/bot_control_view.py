from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.admin_service import AdminService

console = Console()


def run_bot_control_view():
    while True:
        clear_console()

        with get_db() as db:
            service = AdminService(db)
            status = service.get_bot_status()

        status_text = "[bold green]აქტიური (Running)[/bold green]" if status["is_running"] else "[yellow]ლოდინის რეჟიმში (Standby)[/yellow]"

        table = Table.grid(padding=(0, 2))
        table.add_column("პარამეტრი", style="bold cyan")
        table.add_column("მნიშვნელობა", justify="right")

        table.add_row("ბოტის სტატუსი:", status_text)
        table.add_row("მოლოდინში მყოფი (PENDING) ორდერები:", f"[bold yellow]{status['pending_orders']}[/bold yellow]")
        table.add_row("აქტიური ფასის შეტყობინებები:", f"[bold cyan]{status['active_alerts']}[/bold cyan]")

        panel = Panel(
            table,
            title="[bold magenta]სავაჭრო ბოტის (OrderBotEngine) კონტროლი[/bold magenta]",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print(panel)

        console.print("\n1. ორდერების შესრულების შემოწმების იძულებით გაშვება (Force Check)")
        console.print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ: ").strip()

        if choice == "1":
            console.print("\nმიმდინარეობს ორდერების შემოწმება და შესრულება...")
            with get_db() as db:
                service = AdminService(db)
                service.force_run_bot_cycle()
            console.print("[green]შემოწმების ციკლი წარმატებით დასრულდა![/green]")
            input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
        elif choice == "0":
            break
        else:
            console.print("[red]არასწორი არჩევანი.[/red]")
