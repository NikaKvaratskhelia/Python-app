from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console, run_live_loop
from services.user_service import UserService

console = Console()


def show_live_account_stats(user_id: int):
    console.print(
        "\n[bold cyan]ანგარიშის სტატისტიკა & აქტივობა (LIVE განახლება)[/bold cyan]"
    )
    console.print("[dim]გამოსასვლელად დააჭირეთ [Enter] ან [Ctrl+C]...[/dim]\n")

    def build_table() -> Table:
        with get_db() as db:
            user_svc = UserService(db)
            res = user_svc.get_account_stats(user_id)
            stats = res.value if res.is_success else {}

        table = Table(
            title="ანგარიშის აქტივობა & პორტფოლიო (LIVE)",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("მაჩვენებელი", style="cyan")
        table.add_column("მნიშვნელობა", justify="right", style="bold white")

        fiat = stats.get("fiat_balance", 0)
        dep = stats.get("total_deposited", 0)

        table.add_row("ფიატ ბალანსი", f"${fiat:,.2f}")
        table.add_row("ჯამური დეპოზიტი", f"${dep:,.2f}")
        table.add_row("სულ ტრანზაქციები", str(stats.get("total_transactions", 0)))
        table.add_row("შესრულებული ვაჭრობები", str(stats.get("trades_count", 0)))
        table.add_row(
            "აქტიური ორდერები (PENDING)",
            f"[cyan]{stats.get('active_orders', 0)}[/cyan]",
        )
        table.add_row(
            "არსებული აქტივების სახეობა",
            str(stats.get("holding_assets_count", 0)),
        )
        return table

    run_live_loop(build_table, console=console)
    console.print("\n[yellow]სტატისტიკის მონიტორინგი შეჩერდა.[/yellow]")
