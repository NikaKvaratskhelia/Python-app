from core.session_storage import clear_session
from core.helpers import clear_console


def run_user_menu(session_data: dict):
    clear_console()

    while True:
        print(f"\n--- მომხმარებლის პანელი ({session_data.get('username')}) ---")

        print("1. ჩემი პროფილის ნახვა")
        print("2. გასვლა (Logout)")

        choice = input("აირჩიე (1-2): ").strip()

        if choice == "1":
            clear_console()

            print(f"იუზერნეიმი: {session_data.get('username')}")
            print(f"როლი: {session_data.get('role')}")

        elif choice == "2":
            clear_console()
            clear_session()

            print("გამოდედით სისტემიდან.")

            break
        else:
            clear_console()

            print("არასწორი არჩევანი.")
