from decimal import Decimal
from rich.console import Console
from core.database import get_db
from core.helpers import clear_console
from core.result import Result
from services.wallet_service import WalletService
from presentation.user.market.live_market_view import run_live_asset_preview

console = Console()


def run_buy_menu(user_id: int):
    clear_console()
    symbol = (
        input("შეიყვანეთ კრიპტოვალუტის სიმბოლო (მაგ: BTC, ETH, SOL): ")
        .strip()
        .upper()
    )
    if not symbol:
        return

    clear_console()
    live_price = run_live_asset_preview(symbol, action_title="ყიდვა")
    if live_price is None:
        return

    amount_str = input(f"\nშეიყვანეთ რაოდენობა შესასყიდად ({symbol}): ").strip()
    parse_result = Result.try_catch(
        lambda: Decimal(amount_str),
        lambda _: "არასწორი რაოდენობის ფორმატი.",
    )
    if parse_result.is_failure:
        console.print(f"[red]შეცდომა: {parse_result.error}[/red]")
        return

    with get_db() as db:
        service = WalletService(db)
        buy_result = service.buy_asset(
            user_id, symbol, parse_result.value, live_price
        )

    if buy_result.is_success:
        console.print(
            f"[green]წარმატებით იყიდეთ {parse_result.value} {symbol} (${live_price:,.2f}-იანი Live ფასით)![/green]"
        )
    else:
        console.print(f"[red]შეცდომა: {buy_result.error}[/red]")

    input("\nდააჭირეთ Enter-ს გასაგრძელებლად...")
    clear_console()
