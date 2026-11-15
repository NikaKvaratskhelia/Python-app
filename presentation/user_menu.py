from infrastructure.security.session_storage import clear_session
from core.helpers import clear_console
from presentation.orders_menu import order_menu
from presentation.wallet_menu import wallet_menu
from presentation.market_menu import market_menu
from presentation.profile_menu import profile_menu


def run_user_menu(session_data: dict):
    clear_console()

    user_id = session_data.get("user_id")

    while True:
        username = session_data.get("username")
        print(f"\n--- მომხმარებლის პანელი ({username}) ---")

        print("1. ჩემი პროფილის მართვა")
        print("2. ჩემი საფულე (ბალანსი და აქტივები)")
        print("3. კრიპტო ბაზარი და ვაჭრობა")
        print("4. ლიმიტირებული ორდერები")
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
            print("არასწორი არჩევანი.")
