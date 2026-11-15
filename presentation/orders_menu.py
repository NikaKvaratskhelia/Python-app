from decimal import Decimal
from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from infrastructure.persistence.models.order_model import OrderType
from services.order_service import OrderService

console = Console()


def order_menu(user_id: int, username: str):
    while True:
        print(f"\n--- ორდერების მართვა და ვაჭრობა ({username}) ---")
        print("1. ორდერების ნახვა (ფილტრაციით: ALL, PENDING, EXECUTED, CANCELLED)")
        print("2. ახალი ორდერის შექმნა (BUY_LIMIT, SELL_LIMIT, STOP_LOSS, TAKE_PROFIT)")
        print("3. ორდერის გაუქმება (Cancel Order)")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            clear_console()
            print("\nაირჩიეთ ფილტრი:")
            print("1. ყველა ორდერი (ALL)")
            print("2. მოლოდინში (PENDING)")
            print("3. შესრულებული (EXECUTED)")
            print("4. გაუქმებული (CANCELLED)")
            print("0. უკან")

            f_choice = input("აირჩიეთ (1-4, default 1): ").strip()
            if f_choice == "0":
                continue

            filter_map = {
                "1": "ALL",
                "2": "PENDING",
                "3": "EXECUTED",
                "4": "CANCELLED",
            }
            status_filter = filter_map.get(f_choice, "ALL")

            clear_console()
            with get_db() as db:
                order_svc = OrderService(db)
                orders = order_svc.get_orders(user_id, status_filter)

                if not orders:
                    console.print(
                        f"\n[dim]ორდერები სტატუსით '{status_filter}' არ მოიძებნა.[/dim]"
                    )
                else:
                    table = Table(
                        title=f"📋 ორდერების სია [{status_filter}]",
                        show_header=True,
                        header_style="bold magenta",
                    )
                    table.add_column("ID", justify="right", style="dim", width=5)
                    table.add_column("ტიპი", style="bold")
                    table.add_column("სიმბოლო", style="bold cyan")
                    table.add_column("რაოდენობა", justify="right")
                    table.add_column("სამიზნე ფასი ($)", justify="right")
                    table.add_column("სტატუსი", justify="center")

                    for ord in orders:
                        type_color = (
                            "green"
                            if ord.order_type == "BUY_LIMIT"
                            else (
                                "yellow"
                                if ord.order_type == "SELL_LIMIT"
                                else "red" if ord.order_type == "STOP_LOSS" else "cyan"
                            )
                        )
                        status_color = (
                            "cyan"
                            if ord.status == "PENDING"
                            else "green" if ord.status == "EXECUTED" else "red"
                        )
                        table.add_row(
                            str(ord.id),
                            f"[{type_color}]{ord.order_type}[/{type_color}]",
                            f"{ord.symbol}/USDT",
                            f"{ord.amount}",
                            f"${ord.target_price:,.2f}",
                            f"[{status_color}]{ord.status}[/{status_color}]",
                        )

                    console.print(table)

        elif choice == "2":
            clear_console()
            print("\nაირჩიეთ ორდერის ტიპი:")
            print("1. BUY_LIMIT   (ყიდვა, როცა საბაზრო ფასი დაეცემა სამიზნე ფასამდე)")
            print(
                "2. SELL_LIMIT  (გაყიდვა, როცა საბაზრო ფასი გაიზრდება სამიზნე ფასამდე)"
            )
            print("3. STOP_LOSS   (დამცავი გაყიდვა, როცა ფასი დაეცემა სამიზნე ფასამდე)")
            print(
                "4. TAKE_PROFIT (მოგების დაფიქსირება, როცა ფასი მიაღწევს სამიზნე ფასს)"
            )
            print("0. უკან დაბრუნება")

            type_choice = input("აირჩიეთ (1-4): ").strip()
            type_map = {
                "1": OrderType.BUY_LIMIT.value,
                "2": OrderType.SELL_LIMIT.value,
                "3": OrderType.STOP_LOSS.value,
                "4": OrderType.TAKE_PROFIT.value,
            }
            if type_choice not in type_map:
                if type_choice != "0":
                    console.print("[red]არასწორი არჩევანი.[/red]")
                continue

            order_type = type_map[type_choice]

            symbol = (
                input("კრიპტოვალუტის სიმბოლო (მაგ: BTC, ETH, SOL): ").strip().upper()
            )
            if not symbol:
                console.print("[red]სიმბოლო არ შეიძლება იყოს ცარიელი.[/red]")
                continue

            amount_str = input(f"რაოდენობა ({symbol}): ").strip()
            amount_res = Result.try_catch(
                lambda: Decimal(amount_str),
                lambda _: "არასწორი რაოდენობის ფორმატი.",
            )
            if amount_res.is_failure:
                console.print(f"[red]შეცდომა: {amount_res.error}[/red]")
                continue

            price_str = input("სამიზნე ფასი ($): ").strip()
            price_res = Result.try_catch(
                lambda: Decimal(price_str), lambda _: "არასწორი ფასის ფორმატი."
            )
            if price_res.is_failure:
                console.print(f"[red]შეცდომა: {price_res.error}[/red]")
                continue

            with get_db() as db:
                order_svc = OrderService(db)
                create_res = order_svc.create_order(
                    user_id=user_id,
                    symbol=symbol,
                    order_type=order_type,
                    amount=amount_res.value,
                    target_price=price_res.value,
                )

            if create_res.is_success:
                ord = create_res.value
                console.print(
                    f"\n[green]წარმატებით შეიქმნა {ord.order_type} ორდერი #{ord.id} {ord.symbol}-ზე (${ord.target_price:,.2f})![/green]"
                )
                console.print("[dim]შესაბამისი ბალანსი/აქტივი დარეზერვებულია.[/dim]")
            else:
                console.print(
                    f"\n[red]შეცდომა ორდერის შექმნისას: {create_res.error}[/red]"
                )

        elif choice == "3":
            clear_console()
            with get_db() as db:
                order_svc = OrderService(db)
                pending_orders = order_svc.get_orders(user_id, "PENDING")

                if not pending_orders:
                    console.print(
                        "\n[dim]აქტიური (PENDING) ორდერები არ გაქვთ გასაუქმებლად.[/dim]"
                    )
                    continue

                table = Table(
                    title="⚠️ თქვენი აქტიური (PENDING) ორდერები",
                    show_header=True,
                    header_style="bold magenta",
                )
                table.add_column("ID", justify="right", style="bold white", width=5)
                table.add_column("ტიპი", style="bold")
                table.add_column("სიმბოლო", style="bold cyan")
                table.add_column("რაოდენობა", justify="right")
                table.add_column("სამიზნე ფასი ($)", justify="right")

                for ord in pending_orders:
                    type_color = (
                        "green"
                        if ord.order_type == "BUY_LIMIT"
                        else (
                            "yellow"
                            if ord.order_type == "SELL_LIMIT"
                            else "red" if ord.order_type == "STOP_LOSS" else "cyan"
                        )
                    )
                    table.add_row(
                        str(ord.id),
                        f"[{type_color}]{ord.order_type}[/{type_color}]",
                        f"{ord.symbol}/USDT",
                        f"{ord.amount}",
                        f"${ord.target_price:,.2f}",
                    )
                console.print(table)

                cancel_id_str = input(
                    "\nშეიყვანეთ გასაუქმებელი ორდერის ID (ან 0 უკან გამოსასვლელად): "
                ).strip()
                if cancel_id_str in ("0", ""):
                    continue

                parse_id = Result.try_catch(
                    lambda: int(cancel_id_str),
                    lambda _: "ID უნდა იყოს მთელი რიცხვი.",
                )
                if parse_id.is_failure:
                    console.print(f"[red]შეცდომა: {parse_id.error}[/red]")
                    continue

                cancel_res = order_svc.cancel_order(parse_id.value, user_id)
                if cancel_res.is_success:
                    ord = cancel_res.value
                    console.print(
                        f"\n[green]ორდერი #{ord.id} ({ord.symbol} {ord.order_type}) წარმატებით გაუქმდა![/green]"
                    )
                    console.print(
                        "[dim]დარეზერვებული თანხა/აქტივი დაგიბრუნდათ საფულეში.[/dim]"
                    )
                else:
                    console.print(f"\n[red]შეცდომა: {cancel_res.error}[/red]")

        elif choice == "0":
            clear_console()
            break
        else:
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
