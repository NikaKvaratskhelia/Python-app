from core.database import get_db
from infrastructure.persistence.models.price_alert_model import PriceAlertModel
from infrastructure.security.session_storage import clear_session
from core.helpers import clear_console
from presentation.user.profile.profile_menu import profile_menu
from presentation.user.wallet.wallet_menu import wallet_menu
from presentation.user.market.market_menu import market_menu
from presentation.user.orders.orders_menu import order_menu


def run_user_menu(session_data: dict):
    clear_console()

    raw_user_id = session_data.get("user_id")
    user_id = int(raw_user_id) if raw_user_id is not None else None

    while True:
        clear_console()
        username = session_data.get("username")

        if user_id:
            try:
                with get_db() as db:
                    triggered_alerts = (
                        db.query(PriceAlertModel)
                        .filter(
                            PriceAlertModel.user_id == user_id,
                            PriceAlertModel.is_triggered == True,
                        )
                        .all()
                    )
                    if triggered_alerts:
                        for al in triggered_alerts:
                            print(
                                f"[ALERT] {al.symbol}/USDT-მ მიაღწია სამიზნე ფასს: ${al.target_price:,.2f} (პირობა: {al.condition})!"
                            )
            except Exception:
                pass

        print(f"\n--- მომხმარებლის პანელი ({username}) ---")
        print("1. ჩემი პროფილის მართვა")
        print("2. ჩემი საფულე (ბალანსი და აქტივები - LIVE)")
        print("3. კრიპტო ბაზარი და ვაჭრობა (LIVE)")
        print("4. ლიმიტირებული ორდერები (LIVE)")
        print("5. სისტემიდან გამოსვლა (Logout)")
        print("0. აპლიკაციიდან გასვლა (Exit)")

        choice = input("აირჩიე (0-5): ").strip()

        if choice == "1":
            clear_console()
            session_data = profile_menu(session_data)
            username = session_data.get("username")
            clear_console()

        elif choice == "2":
            clear_console()
            if not user_id:
                print("შეცდომა: სესიაში ვერ მოიძებნა იუზერის ID.")
                continue

            wallet_menu(user_id=user_id, username=username)
            clear_console()

        elif choice == "3":
            clear_console()
            if not user_id:
                print("შეცდომა: სესიაში ვერ მოიძებნა იუზერის ID.")
                continue

            market_menu(user_id=user_id, username=username)
            clear_console()

        elif choice == "4":
            clear_console()
            if not user_id:
                print("შეცდომა: სესიაში ვერ მოიძებნა იუზერის ID.")
                continue

            order_menu(user_id=user_id, username=username)
            clear_console()

        elif choice == "5":
            clear_console()
            clear_session()
            print("გამოხვედით სისტემიდან.")
            return "logout"

        elif choice == "0":
            clear_console()
            print("ნახვამდის!")
            return "exit"

        else:
            clear_console()
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
