from decimal import Decimal
from core.database import get_db
from services.wallet_service import WalletService
from core.result import Result


def wallet_menu(user_id: int, username: str):
    while True:
        print(f"\n--- ჩემი საფულე ({username}) ---")
        print("1. ბალანსისა და აქტივების ნახვა")
        print("2. დეპოზიტი (თანხის შეტანა)")
        print("3. ტრანზაქციების ისტორია")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            with get_db() as db:
                service = WalletService(db)
                summary = service.get_portfolio_summary(user_id)

                print(f"\nბალანსი: ${summary['fiat_balance']:,.2f}")

                print(
                    f"კრიპტო აქტივების ღირებულება: ${summary['total_crypto_value']:,.2f}"
                )

                print("\n")

                print(
                    f"**პორტფოლიოს ჯამური ღირებულება: ${summary['total_portfolio_value']:,.2f}**"
                )

                print("\nაქტივები და PnL (მოგება/ზარალი):")

                if not summary["assets"]:
                    print("  (აქტივები არ გაქვთ)")

                for item in summary["assets"]:
                    pnl_sign = "+" if item["pnl_usd"] >= 0 else ""
                    print(
                        f"  - {item['symbol']}: {item['amount']}\n"
                        f"    ფასი: ${item['current_price']:,.2f} | ღირებულება: ${item['current_value']:,.2f}\n"
                        f"    საშ. ყიდვა: ${item['average_buy_price']:,.2f}\n"
                        f"    PnL: {pnl_sign}${item['pnl_usd']:,.2f} ({pnl_sign}{item['pnl_percent']:.2f}%)"
                    )
                    print("-" * 40)

        elif choice == "2":
            amount_str = input("შეიყვანეთ დეპოზიტის თანხა ($): ").strip()
            parse_result = Result.try_catch(
                lambda: Decimal(amount_str), lambda _: "არასწორი თანხის ფორმატი."
            )
            if parse_result.is_failure:
                print(f"შეცდომა: {parse_result.error}")
                continue

            with get_db() as db:
                service = WalletService(db)
                result = service.deposit(user_id, parse_result.value)

            if result.is_success:
                print("დეპოზიტი წარმატებით განთავსდა!")
            else:
                print(f"შეცდომა: {result.error}")

        elif choice == "3":
            with get_db() as db:
                service = WalletService(db)
                wallet = service.get_or_create_wallet(user_id)

                print("\nტრანზაქციების ისტორია:")

                if not wallet.transactions:
                    print("  (ტრანზაქციები არ მოიძებნა)")
                for tx in wallet.transactions:
                    print(
                        f"[{tx.created_at}] {tx.type} | {tx.amount} {tx.symbol or 'USD'} @ ${tx.price}"
                    )

        elif choice == "0":
            break
        else:
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
