from core.helpers import clear_console
from presentation.user.profile.profile_details_view import show_profile_details
from presentation.user.profile.account_stats_view import show_live_account_stats
from presentation.user.profile.change_password_menu import run_change_password_menu
from presentation.user.profile.change_username_menu import run_change_username_menu


def profile_menu(session_data: dict) -> dict:
    user_id = int(session_data.get("user_id"))

    while True:
        clear_console()
        username = session_data.get("username")

        print(f"\n--- პროფილის მართვა ({username}) ---")

        print("1. პროფილის დეტალების ნახვა")
        print("2. ანგარიშის სტატისტიკა და აქტივობა (LIVE)")
        print("3. პაროლის შეცვლა")
        print("4. მომხმარებლის სახელის (Username) შეცვლა")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            show_profile_details(user_id)

        elif choice == "2":
            clear_console()
            show_live_account_stats(user_id)

        elif choice == "3":
            run_change_password_menu(user_id)

        elif choice == "4":
            session_data = run_change_username_menu(session_data)

        elif choice == "0":
            clear_console()
            break
        else:
            clear_console()
            print("არასწორი არჩევანი, სცადეთ თავიდან.")

    return session_data
