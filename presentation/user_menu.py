from core.session_storage import clear_session
from core.helpers import clear_console
from presentation.wallet_menu import wallet_menu


def run_user_menu(session_data: dict):
    clear_console()

    user_id = session_data.get("id")
    username = session_data.get("username")

    while True:
        print(f"\n--- მომხმარებლის პანელი ({username}) ---")

        print("1. ჩემი პროფილის ნახვა")
        print("2. საფულე და პორტფოლიო")
        print("3. გასვლა (Logout)")

        choice = input("აირჩიე (1-3): ").strip()

        if choice == "1":
            clear_console()

            print(f"იუზერნეიმი: {username}")
            print(f"როლი: {session_data.get('role')}")

        elif choice == "2":
            clear_console()
            if not user_id:
                print("შეცდომა: სესიაში ვერ მოიძებნა იუზერის ID.")
                continue

            wallet_menu(user_id=user_id, username=username)
            clear_console()

        elif choice == "3":
            clear_console()
            clear_session()

            print("გამოდედით სისტემიდან.")

            break
        else:
            clear_console()

            print("არასწორი არჩევანი.")
