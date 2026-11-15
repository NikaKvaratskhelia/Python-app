from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.leaderboard_service import LeaderboardService

console = Console()


def show_leaderboard_view(limit: int = 10):
    clear_console()

    with get_db() as db:
        board = LeaderboardService.get_leaderboard(db, limit=limit)

    table = Table(
        title="პლატფორმის საუკეთესო ტრეიდერების ლიდერბორდი (Top Traders)",
        header_style="bold magenta",
        border_style="yellow",
    )
    table.add_column("ადგილი", justify="center", width=8)
    table.add_column("ტრეიდერი", style="bold cyan")
    table.add_column("პორტფოლიო (Net Worth)", justify="right", style="bold green")
    table.add_column("Fiat ბალანსი", justify="right", style="green")
    table.add_column("კრიპტო ღირებულება", justify="right", style="yellow")
    table.add_column("ვაჭრობები", justify="center")
    table.add_column("სავაჭრო მოცულობა", justify="right")
    table.add_column("მთავარი აქტივი", style="dim")

    for entry in board:
        rank = entry["rank"]
        if rank == 1:
            rank_str = "[bold yellow]#1 (TOP)[/bold yellow]"
        elif rank == 2:
            rank_str = "[bold white]#2[/bold white]"
        elif rank == 3:
            rank_str = "[bold red]#3[/bold red]"
        else:
            rank_str = f"#{rank}"

        table.add_row(
            rank_str,
            entry["username"],
            f"${entry['net_worth']:,.2f}",
            f"${entry['fiat_balance']:,.2f}",
            f"${entry['crypto_value']:,.2f}",
            str(entry["trades_count"]),
            f"${entry['trading_volume']:,.2f}",
            entry["top_asset"],
        )

    console.print(table)
    input("\nდააჭირეთ Enter-ს უკან დასაბრუნებლად...")
    clear_console()
