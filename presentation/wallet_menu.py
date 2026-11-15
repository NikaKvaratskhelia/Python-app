from decimal import Decimal
from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.wallet_service import WalletService
from core.result import Result

console = Console()


def wallet_menu(user_id: int, username: str):
    while True:
        print(f"\n--- ჩემი საფულე ({username}) ---")
        print("1. ბალანსისა და აქტივების ნახვა")
        print("2. დეპოზიტი (თანხის შეტანა)")
        print("3. ტრანზაქციების ისტორია")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            clear_console()
            print("\nმიმდინარეობს მონაცემების ჩატვირთვა...")
            with get_db() as db:
                service = WalletService(db)
                summary = service.get_portfolio_summary(user_id)

            clear_console()
            console.print(
                f"\n[bold]ფიატ ბალანსი:[/bold] [green]${summary['fiat_balance']:,.2f}[/green]"
            )
            console.print(
                f"[bold]კრიპტო აქტივების ღირებულება:[/bold] ${summary['total_crypto_value']:,.2f}"
            )
            console.print(
                f"[bold cyan]პორტფოლიოს ჯამური ღირებულება:[/bold cyan] [bold underline]${summary['total_portfolio_value']:,.2f}[/bold underline]\n"
            )

            if not summary["assets"]:
                console.print("  [dim](აქტივები არ გაქვთ)[/dim]")
            else:
                table = Table(
                    title="თქვენი კრიპტო აქტივები & PnL",
                    show_header=True,
                    header_style="bold magenta",
                )
                table.add_column("აქტივი", style="bold cyan")
                table.add_column("რაოდენობა", justify="right", style="bold white")
                table.add_column("მიმდინარე ფასი", justify="right")
                table.add_column("ღირებულება", justify="right")
                table.add_column("საშ. ყიდვა", justify="right")
                table.add_column("PnL ($)", justify="right")
                table.add_column("PnL (%)", justify="right")

                for item in summary["assets"]:
                    pnl_sign = "+" if item["pnl_usd"] >= 0 else ""
                    color = "green" if item["pnl_usd"] >= 0 else "red"
                    cur_price = item["current_price"]
                    avg_price = item["average_buy_price"]
                    cur_price_str = (
                        f"${cur_price:,.6f}" if cur_price < 1 else f"${cur_price:,.2f}"
                    )
                    avg_price_str = (
                        f"${avg_price:,.6f}" if avg_price < 1 else f"${avg_price:,.2f}"
                    )

                    table.add_row(
                        item["symbol"],
                        f"{item['amount']}",
                        cur_price_str,
                        f"${item['current_value']:,.2f}",
                        avg_price_str,
                        f"[{color}]{pnl_sign}${item['pnl_usd']:,.2f}[/{color}]",
                        f"[{color}]{pnl_sign}{item['pnl_percent']:.2f}%[/{color}]",
                    )

                console.print(table)

        elif choice == "2":
            clear_console()
            amount_str = input("შეიყვანეთ დეპოზიტის თანხა ($): ").strip()
            parse_result = Result.try_catch(
                lambda: Decimal(amount_str), lambda _: "არასწორი თანხის ფორმატი."
            )
            if parse_result.is_failure:
                console.print(f"[red]შეცდომა: {parse_result.error}[/red]")
                continue

            with get_db() as db:
                service = WalletService(db)
                result = service.deposit(user_id, parse_result.value)

            if result.is_success:
                console.print("[green]დეპოზიტი წარმატებით განთავსდა![/green]")
            else:
                console.print(f"[red]შეცდომა: {result.error}[/red]")

        elif choice == "3":
            clear_console()

            with get_db() as db:
                service = WalletService(db)
                wallet = service.get_or_create_wallet(user_id)

                if not wallet.transactions:
                    console.print("\n[dim](ტრანზაქციები არ მოიძებნა)[/dim]")
                else:
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
                            if tx.type in ("DEPOSIT", "BUY")
                            else "yellow"
                            if tx.type == "SELL"
                            else "white"
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

        elif choice == "0":
            clear_console()

            break
        else:
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
