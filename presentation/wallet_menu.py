from decimal import Decimal
from core.database import get_db
from services.wallet_service import WalletService


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
                wallet = service.get_or_create_wallet(user_id)

                print(f"\nფიატ ბალანსი: ${wallet.fiat_balance:,.2f}")
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
