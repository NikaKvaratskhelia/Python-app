from decimal import Decimal
from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from services.alert_service import AlertService
from services.binance_ws import BinanceWSManager

console = Console()


def run_create_alert_menu(user_id: int):
    clear_console()
    sym = input("სიმბოლო (მაგ: BTC, ETH): ").strip().upper()
    if not sym:
        return

    cur_price = BinanceWSManager.get_price(sym)
    if cur_price:
        console.print(f"მიმდინარე საბაზრო ფასი: [bold cyan]${cur_price:,.2f}[/bold cyan]")

    target_str = input("სამიზნე ფასი ($): ").strip()
    target_res = Result.try_catch(
        lambda: Decimal(target_str), lambda _: "არასწორი ფასის ფორმატი."
    )
    if target_res.is_failure:
        console.print(f"[red]შეცდომა: {target_res.error}[/red]")
        input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
        clear_console()
        return

    print("პირობა:")
    print("1. როცა ფასი ავა სამიზნეზე ზემოთ (ABOVE)")
    print("2. როცა ფასი დაეცემა სამიზნეზე ქვემოთ (BELOW)")
    cond_input = input("აირჩიეთ (1/2): ").strip()
    cond = "ABOVE" if cond_input == "1" else "BELOW" if cond_input == "2" else ""
    if not cond:
        console.print("[red]არასწორი პირობა.[/red]")
        input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
        clear_console()
        return

    with get_db() as db:
        alert_svc = AlertService(db)
        create_res = alert_svc.create_alert(user_id, sym, target_res.value, cond)

    if create_res.is_success:
        console.print(f"[green]შეტყობინება {sym}-ზე წარმატებით შეიქმნა![/green]")
    else:
        console.print(f"[red]შეცდომა: {create_res.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
