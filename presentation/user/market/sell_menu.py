from decimal import Decimal
from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from services.wallet_service import WalletService
from services.fee_service import FeeService
from presentation.user.market.live_market_view import run_live_asset_preview

console = Console()


def run_sell_menu(user_id: int):
    clear_console()
    symbol = (
        input("კრიპტოვალუტის სიმბოლო გასაყიდად (მაგ: BTC, ETH): ")
        .strip()
        .upper()
    )
    if not symbol:
        return

    clear_console()
    live_price = run_live_asset_preview(symbol, action_title="გაყიდვა")
    if live_price is None:
        return

    amount_str = input(
        f"\nრაოდენობა რამდენი გსურთ გაყიდვა ({symbol}): "
    ).strip()
    parse_result = Result.try_catch(
        lambda: Decimal(amount_str), lambda _: "არასწორი რაოდენობის ფორმატი."
    )
    if parse_result.is_failure:
        console.print(f"[red]შეცდომა: {parse_result.error}[/red]")
        input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
        clear_console()
        return

    gross_val = parse_result.value * live_price
    fee = FeeService.calculate_fee(gross_val)
    net_val = gross_val - fee

    with get_db() as db:
        service = WalletService(db)
        sell_result = service.sell_asset(
            user_id, symbol, parse_result.value, live_price, fee=fee
        )

    if sell_result.is_success:
        console.print(
            f"[green]წარმატებით გაყიდეთ {parse_result.value} {symbol} (${live_price:,.2f}-იანი Live ფასით)![/green]"
        )
        console.print(
            f"[dim]სავაჭრო ღირებულება: ${gross_val:,.2f} | პლატფორმის საკომისიო (0.1%): ${fee:,.2f} | ჩაგერიცხათ: ${net_val:,.2f}[/dim]"
        )
    else:
        console.print(f"[red]შეცდომა: {sell_result.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
