from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from services.admin_service import AdminService

console = Console()


def run_change_role_menu(admin_user_id: int):
    clear_console()
    console.print("[bold cyan]=== მომხმარებლის როლის შეცვლა ===[/bold cyan]\n")

    user_id_str = input("შეიყვანეთ სამიზნე მომხმარებლის ID (ან 0 უკან გამოსასვლელად): ").strip()
    if not user_id_str.isdigit() or int(user_id_str) == 0:
        return

    target_user_id = int(user_id_str)

    console.print("\nაირჩიეთ ახალი როლი:")
    console.print("1. ADMIN (ადმინისტრატორი)")
    console.print("2. REGULAR (ჩვეულებრივი მომხმარებელი)")
    console.print("0. გაუქმება")

    role_choice = input("აირჩიეთ: ").strip()
    if role_choice == "1":
        new_role = "ADMIN"
    elif role_choice == "2":
        new_role = "REGULAR"
    else:
        return

    with get_db() as db:
        service = AdminService(db)
        res = service.change_user_role(target_user_id, new_role, admin_user_id)

    if res.is_success:
        console.print(f"\n[green]მომხმარებელს (#{target_user_id}) წარმატებით მიენიჭა როლი: {new_role}![/green]")
    else:
        console.print(f"\n[red]შეცდომა: {res.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
