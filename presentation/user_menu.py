from rich.console import Console
from rich.table import Table
from core.database import get_db
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.security.session_storage import clear_session
from core.helpers import clear_console
from presentation.orders_menu import order_menu
from presentation.wallet_menu import wallet_menu
from presentation.market_menu import market_menu

console = Console()


def run_user_menu(session_data: dict):
    clear_console()

    user_id = session_data.get("user_id")
    username = session_data.get("username")

    while True:
        print(f"\n--- მომხმარებლის პანელი ({username}) ---")

        print("1. ჩემი პროფილის ნახვა")
        print("2. ჩემი საფულე (ბალანსი და აქტივები)")
        print("3. კრიპტო ბაზარი და ვაჭრობა")
        print("4. ლიმიტირებული ორდერები")
        print("5. სისტემიდან გამოსვლა (Logout)")
        print("0. აპლიკაციიდან გასვლა (Exit)")

        choice = input("აირჩიე (0-5): ").strip()

        if choice == "1":
            clear_console()

            created_at_str = "-"
            role_val = str(session_data.get("role") or "-")

            if user_id:
                try:
                    with get_db() as db:
                        user = (
                            db.query(UserModel)
                            .filter(UserModel.id == int(user_id))
                            .first()
                        )
                        if user and user.created_at:
                            created_at_str = user.created_at.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                        if user and hasattr(user.role, "value"):
                            role_val = user.role.value
                except Exception:
                    pass

            table = Table(
                title="👤 მომხმარებლის პროფილი",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("პარამეტრი", style="cyan")
            table.add_column("მნიშვნელობა", style="bold white")

            table.add_row("ID", str(user_id or "-"))
            table.add_row("მომხმარებელი (Username)", username or "-")
            table.add_row("როლი (Role)", f"[yellow]{role_val.upper()}[/yellow]")
            table.add_row("რეგისტრაციის თარიღი", created_at_str)

            console.print(table)

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
