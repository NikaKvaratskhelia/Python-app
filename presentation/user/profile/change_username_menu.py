from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from services.user_service import UserService

console = Console()


def run_change_username_menu(session_data: dict) -> dict:
    user_id = int(session_data.get("user_id"))

    clear_console()
    print("\n--- მომხმარებლის სახელის (Username) შეცვლა ---")

    new_uname = input("შეიყვანეთ ახალი Username: ").strip()

    if not new_uname:
        clear_console()
        return session_data

    with get_db() as db:
        user_svc = UserService(db)
        res = user_svc.change_username(user_id, new_uname)

    if res.is_success:
        session_data["username"] = res.value
        console.print(
            f"[green]Username წარმატებით შეიცვალა: {res.value}![/green]"
        )
    else:
        console.print(f"[red]შეცდომა: {res.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
    return session_data
