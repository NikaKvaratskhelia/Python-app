from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.user_service import UserService

console = Console()


def show_profile_details(user_id: int):
    clear_console()

    with get_db() as db:
        user_svc = UserService(db)
        res = user_svc.get_profile(user_id)

        if res.is_failure:
            console.print(f"[red]შეცდომა: {res.error}[/red]")
            return

        info = res.value
        date_str = (
            info["created_at"].strftime("%Y-%m-%d %H:%M") if info["created_at"] else "-"
        )

        table = Table(
            title="მომხმარებლის პროფილი",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("პარამეტრი", style="cyan")
        table.add_column("მნიშვნელობა", style="bold white")

        table.add_row("ID", str(info["id"]))
        table.add_row("მომხმარებელი (Username)", info["username"])
        table.add_row("როლი (Role)", f"[yellow]{info['role'].upper()}[/yellow]")
        table.add_row("რეგისტრაციის თარიღი", date_str)

        console.print(table)
        input("\nდააჭირეთ Enter-ს უკან დასაბრუნებლად...")
        clear_console()
