from core.database import get_db
from services.auth_service import AuthService
from core.jwt_manager import create_access_token
from core.session_storage import save_session
from core.helpers import clear_console


def run_auth_menu():
    clear_console()

    while True:
        print("\n--- ავტორიზაციის მენიუ ---")

        print("1. რეგისტრაცია")
        print("2. ლოგინი")
        print("3. უკან დაბრუნება")

        choice = input("აირჩიე (1-3): ").strip()

        if choice == "1":
            clear_console()

            username = input("იუზერნეიმი: ").strip()
            password = input("პაროლი: ").strip()

            with get_db() as db:
                auth_service = AuthService(db)
                result = auth_service.register(username, password)

                if result.is_success:
                    print(f"რეგისტრაცია წარმატებულია: {result._value.username}")
                else:
                    print(result._error)

        elif choice == "2":
            clear_console()

            username = input("იუზერნეიმი: ").strip()
            password = input("პაროლი: ").strip()

            with get_db() as db:
                auth_service = AuthService(db)
                result = auth_service.login(username, password)

                if result.is_success:
                    user = result._value
                    token = create_access_token(
                        user_id=user.id, username=user.username, role=user.role.value
                    )

                    session_data = {
                        "access_token": token,
                        "username": user.username,
                        "role": user.role.value,
                    }

                    save_session(session_data)

                    print(f"ლოგინი წარმატებულია! გამარჯობა {user.username}.")

                    break
                else:
                    print(result._error)

        elif choice == "3":
            clear_console()

            break
        else:
            clear_console()

            print("არასწორი არჩევანი.")
