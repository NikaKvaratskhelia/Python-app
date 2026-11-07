from infrastructure.security.session_storage import clear_session
from core.helpers import clear_console


def run_admin_menu(session_data: dict):
    clear_console()

    while True:
        print(f"\n--- ადმინისტრატორის პანელი ({session_data.get('username')}) ---")

        print("1. ყველა მომხმარებლის მართვა")
        print("2. სისტემური პარამეტრები")
        print("3. გასვლა (Logout)")

        choice = input("აირჩიე (1-3): ").strip()

        if choice == "1":
            clear_console()

            print("აქ იქნება იუზერების სია და მართვა.")
        elif choice == "2":
            clear_console()

            print("სისტემური პარამეტრები...")
        elif choice == "3":
            clear_console()
            clear_session()

            print("გამოდედით სისტემიდან.")

            break
        else:
            clear_console()

            print("არასწორი არჩევანი.")
