from decimal import Decimal
from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from services.admin_service import AdminService

console = Console()


def run_adjust_balance_menu(admin_user_id: int):
    clear_console()
    console.print("[bold cyan]=== მომხმარებლის ბალანსის კორექტირება ===[/bold cyan]\n")

    user_id_str = input("შეიყვანეთ სამიზნე მომხმარებლის ID (ან 0 უკან გამოსასვლელად): ").strip()
    if not user_id_str.isdigit() or int(user_id_str) == 0:
        return

    target_user_id = int(user_id_str)

    amount_str = input("შეიყვანეთ დასარიცხი/ჩამოსაჭრელი თანხა ($) (მაგ: 500 ან -200): ").strip()
    parse_res = Result.try_catch(
        lambda: Decimal(amount_str), lambda _: "არასწორი თანხის ფორმატი."
    )
    if parse_res.is_failure:
        console.print(f"[red]შეცდომა: {parse_res.error}[/red]")
        input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
        return

    amount = parse_res.value

    with get_db() as db:
        service = AdminService(db)
        res = service.adjust_user_balance(target_user_id, amount, admin_user_id)

    if res.is_success:
        action_text = "დაირიცხა" if amount > 0 else "ჩამოიჭრა"
        console.print(
            f"\n[green]მომხმარებელს (#{target_user_id}) წარმატებით {action_text} ${abs(amount):,.2f}! "
            f"ახალი ბალანსი: ${res.value:,.2f}[/green]"
        )
    else:
        console.print(f"\n[red]შეცდომა: {res.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
