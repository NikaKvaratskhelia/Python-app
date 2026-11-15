from decimal import Decimal
from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.wallet_service import WalletService
from infrastructure.persistence.models.order_model import OrderModel
from services.market_service import MarketService

console = Console()


def order_menu(user_id: int, username: str):
    while True:
        print(f"\n--- ლიმიტირებული ორდერები ({username}) ---")
        print("1. აქტიური და ისტორიული ორდერების ნახვა")
        print("2. ახალი ლიმიტირებული ორდერის შექმნა (BUY / SELL)")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            clear_console()

            with get_db() as db:
                service = WalletService(db)
                wallet = service.get_or_create_wallet(user_id)

                orders = (
                    db.query(OrderModel).filter(OrderModel.wallet_id == wallet.id).all()
                )

                if not orders:
                    console.print("\n[dim](ორდერები არ მოიძებნა)[/dim]")
                else:
                    table = Table(
                        title="📋 თქვენი ლიმიტირებული ორდერები",
                        show_header=True,
                        header_style="bold magenta",
                    )
                    table.add_column("ID", justify="right", style="dim", width=4)
                    table.add_column("ტიპი", style="bold")
                    table.add_column("სიმბოლო", style="bold cyan")
                    table.add_column("რაოდენობა", justify="right")
                    table.add_column("სამიზნე ფასი ($)", justify="right")
                    table.add_column("სტატუსი", justify="center")

                    for ord in orders:
                        type_color = (
                            "green" if ord.order_type == "BUY_LIMIT" else "yellow"
                        )
                        status_color = (
                            "cyan"
                            if ord.status == "PENDING"
                            else "green"
                            if ord.status == "EXECUTED"
                            else "red"
                        )
                        table.add_row(
                            str(ord.id),
                            f"[{type_color}]{ord.order_type}[/{type_color}]",
                            ord.symbol,
                            f"{ord.amount}",
                            f"${ord.target_price:,.2f}",
                            f"[{status_color}]{ord.status}[/{status_color}]",
                        )

                    console.print(table)

        elif choice == "2":
            clear_console()

            try:
                print("\nაირჩიეთ ორდერის ტიპი:")
                print("1. BUY_LIMIT (ყიდვა, როცა ფასი დაეცემა)")
                print("2. SELL_LIMIT (გაყიდვა, როცა ფასი აიწევს)")

                type_choice = input("აირჩიეთ (1 ან 2): ").strip()
                if type_choice == "1":
                    order_type = "BUY_LIMIT"
                elif type_choice == "2":
                    order_type = "SELL_LIMIT"
                else:
                    print("არასწორი არჩევანი.")
                    continue

                symbol = (
                    input("კრიპტოვალუტის სიმბოლო (მაგ: BTC, ETH): ").strip().upper()
                )
                amount = Decimal(input(f"რაოდენობა ({symbol}): ").strip())
                target_price = Decimal(input("სამიზნე ფასი ($): ").strip())

                with get_db() as db:
                    service = WalletService(db)
                    wallet = service.get_or_create_wallet(user_id)

                    new_order = OrderModel(
                        wallet_id=wallet.id,
                        symbol=symbol,
                        order_type=order_type,
                        target_price=target_price,
                        amount=amount,
                        status="PENDING",
                    )
                    db.add(new_order)

                print(
                    f"წარმატებით შეიქმნა {order_type} ორდერი {symbol}-ზე (${target_price:,.2f})!"
                )
            except Exception as e:
                print(f"შეცდომა ორდერის შექმნისას: {e}")

        elif choice == "0":
            clear_console()

            break
        else:
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
