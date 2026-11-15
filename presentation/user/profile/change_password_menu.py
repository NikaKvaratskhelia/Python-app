from rich.console import Console
from core.database import get_db
from core.helpers import clear_console, get_masked_password
from services.user_service import UserService

console = Console()


def run_change_password_menu(user_id: int):
    clear_console()
    print("\n--- პაროლის შეცვლა ---")

    current_pw = get_masked_password("შეიყვანეთ მიმდინარე პაროლი: ").strip()

    if not current_pw:
        clear_console()
        return

    new_pw = get_masked_password("შეიყვანეთ ახალი პაროლი: ").strip()
    confirm_pw = get_masked_password("გაიმეორეთ ახალი პაროლი: ").strip()

    if new_pw != confirm_pw:
        console.print("[red]შეცდომა: ახალი პაროლები არ ემთხვევა ერთმანეთს.[/red]")
        return

    with get_db() as db:
        user_svc = UserService(db)
        res = user_svc.change_password(user_id, current_pw, new_pw)

    if res.is_success:
        console.print("[green]პაროლი წარმატებით შეიცვალა![/green]")
    else:
        console.print(f"[red]შეცდომა: {res.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
