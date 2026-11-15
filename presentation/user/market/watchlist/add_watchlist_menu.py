from rich.console import Console
from core.database import get_db
from services.watchlist_service import WatchlistService

console = Console()


def run_add_watchlist_menu(user_id: int):
    new_sym = (
        input("შეიყვანეთ კრიპტოვალუტის სიმბოლო (მაგ: SOL, BTC): ")
        .strip()
        .upper()
    )
    if not new_sym:
        return

    with get_db() as db:
        w_svc = WatchlistService(db)
        add_res = w_svc.add(user_id, new_sym)

    if add_res.is_success:
        console.print(f"[green]{new_sym} წარმატებით დაემატა რჩეულებში![/green]")
    else:
        console.print(f"[red]შეცდომა: {add_res.error}[/red]")
