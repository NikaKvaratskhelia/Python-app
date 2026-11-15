from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from services.watchlist_service import WatchlistService
from presentation.user.market.live_market_view import run_live_market_view
from presentation.user.market.watchlist.add_watchlist_menu import run_add_watchlist_menu
from presentation.user.market.watchlist.remove_watchlist_menu import run_remove_watchlist_menu

console = Console()


def watchlist_menu(user_id: int):
    clear_console()
    with get_db() as db:
        w_svc = WatchlistService(db)
        saved_symbols = w_svc.get_watchlist(user_id)

    if saved_symbols:
        run_live_market_view(
            symbols=saved_symbols,
            title="თქვენი Watchlist (LIVE WebSocket სტრიმი)",
        )
        clear_console()
    else:
        print("\n--- რჩეული მონეტები (Watchlist) ---")
        console.print("[dim]რჩეულებში მონეტები ჯერ არ გაქვთ დამატებული.[/dim]")

    while True:
        clear_console()
        with get_db() as db:
            w_svc = WatchlistService(db)
            current_symbols = w_svc.get_watchlist(user_id)

        print("\n--- Watchlist-ის მართვა ---")
        if current_symbols:
            print("1. რჩეულების LIVE სტრიმის ნახვა")
            print("2. ახალი მონეტის დამატება")
            print("3. მონეტის ამოშლა")
            print("0. უკან დაბრუნება")
            sub_choice = input("\nაირჩიეთ (1/2/3/0): ").strip()
            if sub_choice == "1":
                clear_console()
                run_live_market_view(
                    symbols=current_symbols,
                    title="თქვენი Watchlist (LIVE WebSocket სტრიმი)",
                )
                clear_console()
            elif sub_choice == "2":
                run_add_watchlist_menu(user_id)
            elif sub_choice == "3":
                run_remove_watchlist_menu(user_id)
            elif sub_choice == "0":
                clear_console()
                break
        else:
            print("1. ახალი მონეტის დამატება")
            print("0. უკან დაბრუნება")
            sub_choice = input("\nაირჩიეთ (1/0): ").strip()
            if sub_choice == "1":
                run_add_watchlist_menu(user_id)
            elif sub_choice == "0":
                clear_console()
                break
