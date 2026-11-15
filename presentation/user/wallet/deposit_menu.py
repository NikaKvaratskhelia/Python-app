from decimal import Decimal
from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from services.wallet_service import WalletService

console = Console()


def run_deposit_menu(user_id: int):
    clear_console()

    amount_str = input("შეიყვანეთ დეპოზიტის თანხა ($): ").strip()

    parse_result = Result.try_catch(
        lambda: Decimal(amount_str), lambda _: "არასწორი თანხის ფორმატი."
    )

    if parse_result.is_failure:
        console.print(f"[red]შეცდომა: {parse_result.error}[/red]")
        return

    with get_db() as db:
        service = WalletService(db)
        result = service.deposit(user_id, parse_result.value)

    if result.is_success:
        console.print("[green]დეპოზიტი წარმატებით განთავსდა![/green]")
    else:
        console.print(f"[red]შეცდომა: {result.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
