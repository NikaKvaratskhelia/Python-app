import threading
from infrastructure.security.session_storage import get_session
from presentation.auth_menu import run_auth_menu
from presentation.user_menu import run_user_menu
from presentation.admin_menu import run_admin_menu
from core.helpers import clear_console
from services.order_bot_engine import OrderBotEngine


def start_background_bot():
    """BG ბოტის დამწყები ფუნქცია, რომელიც მუშაობს პარალელურ თრედში"""
    try:
        OrderBotEngine.run_bot(interval_seconds=15)
    except Exception as e:
        print(f"BG ბოტის შეცდომა: {e}")


def main():
    bot_thread = threading.Thread(target=start_background_bot, daemon=True)
    bot_thread.start()

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
