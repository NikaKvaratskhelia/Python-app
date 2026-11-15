from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.wallet_service import WalletService

console = Console()


def run_transactions_menu(user_id: int):
    clear_console()
    with get_db() as db:
        service = WalletService(db)
        wallet = service.get_or_create_wallet(user_id)

        if not wallet.transactions:
            console.print("  [dim](ტრანზაქციების ისტორია ცარიელია)[/dim]")
            input("\nდააჭირეთ Enter-ს უკან დასაბრუნებლად...")
            clear_console()
            return

        table = Table(
            title="ტრანზაქციების ისტორია",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("თარიღი", style="dim")
        table.add_column("ტიპი", style="bold")
        table.add_column("აქტივი", style="bold cyan")
        table.add_column("რაოდენობა", justify="right")
        table.add_column("ფასი ($)", justify="right")

        for tx in wallet.transactions:
            type_color = (
                "green"
                if tx.type in ("DEPOSIT", "BUY", "TRANSFER_IN")
                else (
                    "yellow"
                    if tx.type in ("SELL", "WITHDRAW", "TRANSFER_OUT")
                    else "white"
                )
            )

            date_str = (
                tx.created_at.strftime("%Y-%m-%d %H:%M")
                if hasattr(tx.created_at, "strftime")
                else str(tx.created_at)
            )

            price_str = f"${tx.price:,.2f}" if tx.price else "-"

            table.add_row(
                date_str,
                f"[{type_color}]{tx.type}[/{type_color}]",
                tx.symbol or "USD",
                f"{tx.amount}",
                price_str,
            )

        console.print(table)

        export_choice = (
            input("\nგსურთ ისტორიის CSV ექსპორტი? (y/n): ").strip().lower()
        )
        if export_choice == "y":
            export_res = service.export_transactions_csv(user_id)
            if export_res.is_success:
                console.print(
                    f"[green]ფაილი წარმატებით შეინახა: {export_res.value}[/green]"
                )
            else:
                console.print(
                    f"[red]შეცდომა ექსპორტისას: {export_res.error}[/red]"
                )

        input("\nდააჭირეთ Enter-ს უკან დასაბრუნებლად...")
        clear_console()
