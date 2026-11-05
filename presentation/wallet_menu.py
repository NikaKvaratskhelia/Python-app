from decimal import Decimal
from core.database import get_db
from services.wallet_service import WalletService


def wallet_menu(user_id: int, username: str):
    while True:
        print(f"\n---საფულე და პორტფოლიო ({username}) ---")
        print("1. ბალანსისა და აქტივების ნახვა")
        print("2. დეპოზიტი (თანხის შეტანა)")
        print("3. კრიპტოვალუტის ყიდვა")
        print("4. კრიპტოვალუტის გაყიდვა")
        print("5. ტრანზაქციების ისტორია")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            with get_db() as db:
                service = WalletService(db)

                wallet = service.get_or_create_wallet(user_id)

                print(f"\n ბალანსი: ${wallet.fiat_balance:,.2f}")
                print("აქტივები:")

                if not wallet.assets:
                    print("  (აქტივები არ გაქვთ)")
                for asset in wallet.assets:
                    print(
                        f" - {asset.symbol}: {asset.amount} (საშ. ყიდვის ფასი: ${asset.average_buy_price:,.2f})"
                    )

        elif choice == "2":
            try:
                amount_str = input("შეიყვანეთ დეპოზიტის თანხა ($): ").strip()

                amount = Decimal(amount_str)

                with get_db() as db:
                    service = WalletService(db)
                    service.deposit(user_id, amount)

                print("დეპოზიტი წარმატებით განთავსდა!")
            except Exception as e:
                print(f"შეცდომა: {e}")

        elif choice == "3":
            try:
                symbol = (
                    input("კრიპტოვალუტის სიმბოლო (მაგ: BTC, ETH): ").strip().upper()
                )
                amount = Decimal(input(f"რაოდენობა ({symbol}): ").strip())
                price = Decimal(input(f"ერთეულის ფასი ($): ").strip())

                with get_db() as db:
                    service = WalletService(db)
                    service.buy_asset(user_id, symbol, amount, price)
                print(f"წარმატებით იყიდეთ {amount} {symbol}!")
            except Exception as e:
                print(f"შეცდომა: {e}")

        elif choice == "4":
            try:
                symbol = (
                    input("კრიპტოვალუტის სიმბოლო გასაყიდად (მაგ: BTC, ETH): ")
                    .strip()
                    .upper()
                )

                amount = Decimal(input(f"რაოდენობა ({symbol}): ").strip())

                price = Decimal(input(f"ერთეულის მიმდინარე ფასი ($): ").strip())

                with get_db() as db:
                    service = WalletService(db)
                    service.sell_asset(user_id, symbol, amount, price)

                print(f"წარმატებით გაყიდეთ {amount} {symbol}!")
            except Exception as e:
                print(f"შეცდომა: {e}")

        elif choice == "5":
            with get_db() as db:
                service = WalletService(db)
                wallet = service.get_or_create_wallet(user_id)

                print("\nტრანზაქციების ისტორია:")

                if not wallet.transactions:
                    print("(ტრანზაქციები არ მოიძებნა)")
                for tx in wallet.transactions:
                    print(
                        f"[{tx.created_at}] {tx.type} | {tx.amount} {tx.symbol or 'USD'} @ ${tx.price}"
                    )

        elif choice == "0":
            break
        else:
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
