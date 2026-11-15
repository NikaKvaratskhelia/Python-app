from decimal import Decimal
from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from services.order_service import OrderService
from services.binance_ws import BinanceWSManager

console = Console()


def run_create_order_menu(user_id: int):
    clear_console()

    print("\nაირჩიეთ ორდერის ტიპი:")

    print("1. BUY_LIMIT   (ყიდვა, როცა საბაზრო ფასი დაეცემა სამიზნე ფასამდე)")
    print("2. SELL_LIMIT  (გაყიდვა, როცა საბაზრო ფასი გაიზრდება სამიზნე ფასამდე)")
    print("3. STOP_LOSS   (დამცავი გაყიდვა, როცა ფასი დაეცემა სამიზნე ფასამდე)")
    print("0. უკან დაბრუნება")

    type_choice = input("აირჩიეთ ტიპი (1-3): ").strip()

    if type_choice == "0":
        clear_console()
        return

    type_map = {
        "1": "BUY_LIMIT",
        "2": "SELL_LIMIT",
        "3": "STOP_LOSS",
    }

    order_type = type_map.get(type_choice)

    if not order_type:
        console.print("[red]არასწორი არჩევანი.[/red]")
        return

    symbol = input("კრიპტოვალუტის სიმბოლო (მაგ: BTC, ETH, SOL): ").strip().upper()

    if not symbol:
        console.print("[red]სიმბოლო არ შეიძლება იყოს ცარიელი.[/red]")
        return

    ws_price = BinanceWSManager.get_price(symbol)

    if ws_price:
        console.print(
            f"მიმდინარე საბაზრო ფასი: [bold cyan]${ws_price:,.2f}[/bold cyan]"
        )

    amount_str = input(f"რაოდენობა ({symbol}): ").strip()
    amount_res = Result.try_catch(
        lambda: Decimal(amount_str),
        lambda _: "არასწორი რაოდენობის ფორმატი.",
    )

    if amount_res.is_failure:
        console.print(f"[red]შეცდომა: {amount_res.error}[/red]")
        return

    target_str = input("სამიზნე ფასი ($): ").strip()
    target_res = Result.try_catch(
        lambda: Decimal(target_str),
        lambda _: "არასწორი ფასის ფორმატი.",
    )

    if target_res.is_failure:
        console.print(f"[red]შეცდომა: {target_res.error}[/red]")
        return

    with get_db() as db:
        order_svc = OrderService(db)
        create_res = order_svc.create_order(
            user_id=user_id,
            symbol=symbol,
            order_type=order_type,
            amount=amount_res.value,
            target_price=target_res.value,
        )

    if create_res.is_success:
        ord = create_res.value

        console.print(
            f"\n[green]ორდერი #{ord.id} ({ord.symbol} {ord.order_type}) წარმატებით შეიქმნა![/green]"
        )

        console.print(
            f"სამიზნე ფასი: ${ord.target_price:,.2f} | რაოდენობა: {ord.amount} | სტატუსი: {ord.status}"
        )
    else:
        console.print(f"\n[red]შეცდომა: {create_res.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
