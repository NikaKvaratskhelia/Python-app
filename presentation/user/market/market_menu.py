from core.helpers import clear_console
from presentation.user.market.live_market_view import run_live_market_view
from presentation.user.market.buy_menu import run_buy_menu
from presentation.user.market.sell_menu import run_sell_menu
from presentation.user.market.watchlist.watchlist_menu import watchlist_menu
from presentation.user.market.alerts.alerts_menu import alerts_menu
from presentation.user.market.movers.top_movers_view import show_live_top_movers


def market_menu(user_id: int, username: str):
    user_id = int(user_id)
    while True:
        print(f"\n--- კრიპტო ბაზარი და ვაჭრობა ({username}) ---")
        print("1. კრიპტოვალუტის ფასები (LIVE სტრიმი)")
        print("2. კონკრეტული კრიპტოვალუტის ძებნა და ყიდვა (LIVE პრევიუ)")
        print("3. კრიპტოვალუტის გაყიდვა (LIVE პრევიუ)")
        print("4. რჩეული მონეტები (Watchlist) & მართვა (LIVE)")
        print("5. ფასის შეტყობინებები (Price Alerts - LIVE)")
        print("6. დღის ტოპ ზრდა / ვარდნა (Top Gainers & Losers - LIVE)")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            clear_console()
            run_live_market_view()
            clear_console()

        elif choice == "2":
            run_buy_menu(user_id=user_id)

        elif choice == "3":
            run_sell_menu(user_id=user_id)

        elif choice == "4":
            watchlist_menu(user_id=user_id)

        elif choice == "5":
            alerts_menu(user_id=user_id)

        elif choice == "6":
            clear_console()
            show_live_top_movers(limit=5)
            clear_console()

        elif choice == "0":
            clear_console()
            break
        else:
            clear_console()
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
