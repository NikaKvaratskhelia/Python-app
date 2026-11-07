from infrastructure.security.session_storage import get_session
from presentation.auth_menu import run_auth_menu
from presentation.user_menu import run_user_menu
from presentation.admin_menu import run_admin_menu
from core.helpers import clear_console


def main():
    clear_console()
    print("აპლიკაცია ჩაირთო!")

    while True:
        session = get_session()

        if session:

            role = session.get("role")

            if role == "admin":
                run_admin_menu(session)
            else:
                run_user_menu(session)
        else:
            clear_console()

            print("\n=== მთავარი მენიუ ===")

            print("1. ავტორიზაცია / რეგისტრაცია")
            print("0. გამოსვლა")

            choice = input("აირჩიე: ").strip()

            if choice == "1":
                run_auth_menu()
            elif choice == "0":
                print("ნახვამდის!")
                break
            else:
                print("არასწორი არჩევანი.")


if __name__ == "__main__":
    main()
