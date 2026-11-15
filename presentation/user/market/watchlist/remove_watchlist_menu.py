from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from services.watchlist_service import WatchlistService

console = Console()


def run_remove_watchlist_menu(user_id: int):
    clear_console()
    del_sym = input("შეიყვანეთ ამოსაშლელი სიმბოლო: ").strip().upper()
    if not del_sym:
        return

    with get_db() as db:
        w_svc = WatchlistService(db)
        del_res = w_svc.remove(user_id, del_sym)

    if del_res.is_success:
        console.print(f"[green]{del_sym} ამოიშალა რჩეულებიდან.[/green]")
    else:
        console.print(f"[red]შეცდომა: {del_res.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
