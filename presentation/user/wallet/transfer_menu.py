from decimal import Decimal
from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from services.wallet_service import WalletService

console = Console()


def run_transfer_menu(user_id: int):
    clear_console()
    print("\n--- შიდა P2P გადარიცხვა ---")
    to_username = input("მიმღების Username: ").strip()
    if not to_username:
        console.print("[red]Username არ შეიძლება იყოს ცარიელი.[/red]")
        return

    asset_type = (
        input("რისი გადარიცხვა გსურთ? (USD / კრიპტო, მაგ: BTC, ETH): ")
        .strip()
        .upper()
    )
    if not asset_type:
        console.print("[red]აქტივი არ შეიძლება იყოს ცარიელი.[/red]")
        return

    amount_str = input(f"რაოდენობა ({asset_type}): ").strip()
    parse_result = Result.try_catch(
        lambda: Decimal(amount_str), lambda _: "არასწორი რაოდენობის ფორმატი."
    )
    if parse_result.is_failure:
        console.print(f"[red]შეცდომა: {parse_result.error}[/red]")
        return

    with get_db() as db:
        service = WalletService(db)
        transfer_res = service.transfer(
            from_user_id=user_id,
            to_username=to_username,
            symbol=asset_type,
            amount=parse_result.value,
        )

    if transfer_res.is_success:
        console.print(
            f"[green]წარმატებით გადაირიცხა {parse_result.value} {asset_type} მომხმარებელთან @{to_username}![/green]"
        )
    else:
        console.print(f"[red]შეცდომა: {transfer_res.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
