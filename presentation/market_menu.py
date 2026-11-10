from decimal import Decimal
from core.database import get_db
from services.market_service import MarketService
from services.wallet_service import WalletService
from core.result import Result


def market_menu(user_id: int, username: str):
    while True:
        print(f"\n--- კრიპტო ბაზარი და ვაჭრობა ({username}) ---")
        print("1. ყველა კრიპტოვალუტის ფასები და 24სთ ცვლილება")
        print("2. კონკრეტული კრიპტოვალუტის ძებნა და ყიდვა")
        print("3. კრიპტოვალუტის გაყიდვა")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":

            print("\nმიმდინარეობს ბაზრის მონაცემების წამოღება...")

            market_data = MarketService.get_all_active_prices()

            if not market_data:
                print("ვეღარ მოხერხდა ბაზრის მონაცემების მიღება.")
                continue

            print("\nტოპ კრიპტოვალუტები ბაზარზე:")
            count = 0

            for symbol, info in market_data.items():
                if count >= 20:
                    break

                price = info["price"]
                change = info["change"]
                sign = "+" if change >= 0 else ""

                print(
                    f" - {symbol}/USDT: ${price:,.4f} | ცვლილება (24სთ): {sign}{change}%"
                )

                count += 1

        elif choice == "2":
            symbol = (
                input("შეიყვანეთ კრიპტოვალუტის სიმბოლო (მაგ: BTC, ETH, SOL): ")
                .strip()
                .upper()
            )

            print(f"🔄 მიმდინარეობს {symbol} მონაცემების წამოღება...")

            market_info = MarketService.get_market_stats(symbol)

            if not market_info:
                print(f"სიმბოლო '{symbol}' ვერ მოიძებნა ბაზარზე.")
                continue

            live_price = market_info["price"]
            change = market_info["price_change_percent"]
            sign = "+" if change >= 0 else ""

            print(f"\nაქტივი: {symbol}")
            print(f"მიმდინარე ფასი: ${live_price:,.2f}")
            print(f"24სთ ცვლილება: {sign}{change}%")

            confirm = input(f"\nგსურთ {symbol}-ის ყიდვა? (y/n): ").strip().lower()

            if confirm == "y":
                amount_str = input(f"რაოდენობა ({symbol}): ").strip()
                parse_result = Result.try_catch(
                    lambda: Decimal(amount_str), lambda _: "არასწორი რაოდენობის ფორმატი."
                )
                if parse_result.is_failure:
                    print(f"შეცდომა: {parse_result.error}")
                    continue

                with get_db() as db:
                    service = WalletService(db)
                    buy_result = service.buy_asset(
                        user_id, symbol, parse_result.value, live_price
                    )

                if buy_result.is_success:
                    print(
                        f"წარმატებით იყიდეთ {parse_result.value} {symbol} (${live_price:,.2f}-იანი ფასით)!"
                    )
                else:
                    print(f"შეცდომა: {buy_result.error}")

        elif choice == "3":
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

            amount_str = input(
                f"რაოდენობა რამდენი გსურთ გაყიდვა ({symbol}): "
            ).strip()
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

            if sell_result.is_success:
                print(
                    f"წარმატებით გაყიდეთ {parse_result.value} {symbol} (${live_price:,.2f}-იანი ფასით)!"
                )
            else:
                print(f"შეცდომა: {sell_result.error}")

        elif choice == "0":
            break

        else:
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
