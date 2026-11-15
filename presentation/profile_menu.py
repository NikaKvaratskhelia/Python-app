from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console, get_masked_password
from services.user_service import UserService

console = Console()


def profile_menu(session_data: dict) -> dict:
    user_id = int(session_data.get("user_id"))

    while True:
        username = session_data.get("username")
        print(f"\n--- პროფილის მართვა ({username}) ---")
        print("1. პროფილის დეტალების ნახვა")
        print("2. ანგარიშის სტატისტიკა და აქტივობა")
        print("3. პაროლის შეცვლა")
        print("4. მომხმარებლის სახელის (Username) შეცვლა")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            clear_console()

            with get_db() as db:
                user_svc = UserService(db)
                res = user_svc.get_profile(user_id)

                if res.is_failure:
                    console.print(f"[red]შეცდომა: {res.error}[/red]")
                    continue

                info = res.value
                date_str = (
                    info["created_at"].strftime("%Y-%m-%d %H:%M")
                    if info["created_at"]
                    else "-"
                )

                table = Table(
                    title="მომხმარებლის პროფილი",
                    show_header=True,
                    header_style="bold magenta",
                )
                table.add_column("პარამეტრი", style="cyan")
                table.add_column("მნიშვნელობა", style="bold white")

                table.add_row("ID", str(info["id"]))
                table.add_row("მომხმარებელი (Username)", info["username"])
                table.add_row("როლი (Role)", f"[yellow]{info['role'].upper()}[/yellow]")
                table.add_row("რეგისტრაციის თარიღი", date_str)

                console.print(table)

        elif choice == "2":
            clear_console()
            with get_db() as db:
                user_svc = UserService(db)
                res = user_svc.get_account_stats(user_id)

                if res.is_failure:
                    console.print(f"[red]შეცდომა: {res.error}[/red]")
                    continue

                stats = res.value

                table = Table(
                    title="ანგარიშის სტატისტიკა & აქტივობა",
                    show_header=True,
                    header_style="bold magenta",
                )
                table.add_column("მაჩვენებელი", style="cyan")
                table.add_column("მნიშვნელობა", justify="right", style="bold white")

                table.add_row("ფიატ ბალანსი", f"${stats['fiat_balance']:,.2f}")
                table.add_row("ჯამური დეპოზიტი", f"${stats['total_deposited']:,.2f}")
                table.add_row("სულ ტრანზაქციები", str(stats["total_transactions"]))
                table.add_row("შესრულებული ვაჭრობები", str(stats["trades_count"]))
                table.add_row(
                    "აქტიური ორდერები (PENDING)",
                    f"[cyan]{stats['active_orders']}[/cyan]",
                )
                table.add_row(
                    "ფლობილი აქტივების სახეობა",
                    str(stats["holding_assets_count"]),
                )

                console.print(table)

        elif choice == "3":
            clear_console()
            print("\n--- პაროლის შეცვლა ---")

            current_pw = get_masked_password("შეიყვანეთ მიმდინარე პაროლი: ").strip()

            if not current_pw:
                console.print("[dim]ოპერაცია გაუქმდა.[/dim]")
                continue

            new_pw = get_masked_password("შეიყვანეთ ახალი პაროლი: ").strip()

            if not new_pw:
                console.print("[dim]ოპერაცია გაუქმდა.[/dim]")
                continue

            confirm_pw = get_masked_password("გაიმეორეთ ახალი პაროლი: ").strip()

            if new_pw != confirm_pw:
                console.print(
                    "[red]შეცდომა: ახალი პაროლები არ ემთხვევა ერთმანეთს.[/red]"
                )

                continue

            with get_db() as db:
                user_svc = UserService(db)
                change_res = user_svc.change_password(user_id, current_pw, new_pw)

            if change_res.is_success:
                console.print("\n[green]პაროლი წარმატებით შეიცვალა![/green]")
            else:
                console.print(f"\n[red]შეცდომა: {change_res.error}[/red]")

        elif choice == "4":
            clear_console()
            print("\n--- მომხმარებლის სახელის (Username) შეცვლა ---")

            console.print(f"მიმდინარე სახელი: [bold cyan]{username}[/bold cyan]")

            new_name = input(
                "შეიყვანეთ ახალი იუზერნეიმი (ან 0 უკან გამოსასვლელად): "
            ).strip()

            if new_name in ("0", ""):
                continue

            with get_db() as db:
                user_svc = UserService(db)
                change_res = user_svc.change_username(user_id, new_name)

            if change_res.is_success:

                updated_name = change_res.value
                session_data["username"] = updated_name

                console.print(
                    f"\n[green]მომხმარებლის სახელი წარმატებით შეიცვალა: {updated_name}![/green]"
                )
            else:
                console.print(f"\n[red]შეცდომა: {change_res.error}[/red]")

        elif choice == "0":
            clear_console()
            break
        else:
            print("არასწორი არჩევანი, სცადეთ თავიდან.")

    return session_data
