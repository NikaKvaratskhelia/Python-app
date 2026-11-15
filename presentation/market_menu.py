from decimal import Decimal
from rich.console import Console
from rich.table import Table
from core.database import get_db
from core.helpers import clear_console
from services.market_service import MarketService
from services.wallet_service import WalletService
from core.result import Result

console = Console()


def market_menu(user_id: int, username: str):
    while True:
        print(f"\n--- კრიპტო ბაზარი და ვაჭრობა ({username}) ---")
        print("1. ყველა კრიპტოვალუტის ფასები და 24სთ ცვლილება")
        print("2. კონკრეტული კრიპტოვალუტის ძებნა და ყიდვა")
        print("3. კრიპტოვალუტის გაყიდვა")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            clear_console()

            print("\nმიმდინარეობს ბაზრის მონაცემების წამოღება...")

            market_data = MarketService.get_all_active_prices()
            clear_console()

            if not market_data:
                console.print("[red]ვეღარ მოხერხდა ბაზრის მონაცემების მიღება.[/red]")
                continue

            table = Table(
                title="ტოპ კრიპტოვალუტები ბაზარზე",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("#", justify="right", style="dim", width=4)
            table.add_column("სიმბოლო", style="bold cyan")
            table.add_column("ფასი ($)", justify="right", style="bold white")
            table.add_column("24სთ ცვლილება", justify="right")

            count = 0
            for symbol, info in market_data.items():
                if count >= 20:
                    break

                price = info["price"]
                change = info["change"]
                sign = "+" if change >= 0 else ""
                color = "green" if change >= 0 else "red"
                change_str = f"[{color}]{sign}{change:.2f}%[/{color}]"
                price_str = f"${price:,.6f}" if price < 1 else f"${price:,.2f}"

                table.add_row(str(count + 1), f"{symbol}/USDT", price_str, change_str)
                count += 1

            console.print(table)

        elif choice == "2":
            clear_console()

            symbol = (
                input("შეიყვანეთ კრიპტოვალუტის სიმბოლო (მაგ: BTC, ETH, SOL): ")
                .strip()
                .upper()
            )

            print(f"მიმდინარეობს {symbol} მონაცემების წამოღება...")

            market_info = MarketService.get_market_stats(symbol)
            clear_console()

            if not market_info:
                console.print(f"[red]სიმბოლო '{symbol}' ვერ მოიძებნა ბაზარზე.[/red]")
                continue

            live_price = market_info["price"]
            change = market_info["price_change_percent"]
            sign = "+" if change >= 0 else ""
            color = "green" if change >= 0 else "red"
            price_str = (
                f"${live_price:,.6f}" if live_price < 1 else f"${live_price:,.2f}"
            )

            table = Table(
                title=f"აქტივის დეტალები: {symbol}",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("პარამეტრი", style="cyan")
            table.add_column("მნიშვნელობა", justify="right", style="bold white")
            table.add_row("სიმბოლო", f"{symbol}/USDT")
            table.add_row("მიმდინარე ფასი", price_str)
            table.add_row("24სთ ცვლილება", f"[{color}]{sign}{change:.2f}%[/{color}]")
            console.print(table)

            confirm = input(f"\nგსურთ {symbol}-ის ყიდვა? (y/n): ").strip().lower()

            if confirm == "y":
                amount_str = input(f"რაოდენობა ({symbol}): ").strip()
                parse_result = Result.try_catch(
                    lambda: Decimal(amount_str),
                    lambda _: "არასწორი რაოდენობის ფორმატი.",
                )
                if parse_result.is_failure:
                    console.print(f"[red]შეცდომა: {parse_result.error}[/red]")
                    continue

                with get_db() as db:
                    service = WalletService(db)
                    buy_result = service.buy_asset(
                        user_id, symbol, parse_result.value, live_price
                    )

                if buy_result.is_success:
                    console.print(
                        f"[green]წარმატებით იყიდეთ {parse_result.value} {symbol} (${live_price:,.2f}-იანი ფასით)![/green]"
                    )
                else:
                    console.print(f"[red]შეცდომა: {buy_result.error}[/red]")

        elif choice == "3":
            clear_console()

            symbol = (
                input("კრიპტოვალუტის სიმბოლო გასაყიდად (მაგ: BTC, ETH): ")
                .strip()
                .upper()
            )

            live_price = MarketService.get_crypto_price(symbol)

            if not live_price:
                print(f"ვეღარ მოიძებნა ფასი სიმბოლოსთვის {symbol}.")
                continue

            print(f"მიმდინარე საბაზრო ფასი: ${live_price:,.2f}")

            amount_str = input(f"რაოდენობა რამდენი გსურთ გაყიდვა ({symbol}): ").strip()
            parse_result = Result.try_catch(
                lambda: Decimal(amount_str), lambda _: "არასწორი რაოდენობის ფორმატი."
            )

            if parse_result.is_failure:
                print(f"შეცდომა: {parse_result.error}")
                continue

            with get_db() as db:
                service = WalletService(db)
                sell_result = service.sell_asset(
                    user_id, symbol, parse_result.value, live_price
                )

            clear_console()

            if sell_result.is_success:
                print(
                    f"წარმატებით გაყიდეთ {parse_result.value} {symbol} (${live_price:,.2f}-იანი ფასით)!"
                )
            else:
                print(f"შეცდომა: {sell_result.error}")

        elif choice == "0":
            clear_console()

            break

        else:
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
