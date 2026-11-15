from decimal import Decimal
from core.database import get_db
from core.helpers import clear_console
from services.wallet_service import WalletService
from infrastructure.persistence.models.order_model import OrderModel
from services.market_service import MarketService


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

                print("\nთქვენი ორდერების სია:")

                if not orders:
                    print("(ორდერები არ მოიძებნა)")

                for ord in orders:
                    print(
                        f" - [{ord.id}] {ord.order_type} | {ord.symbol} | "
                        f"რაოდენობა: {ord.amount} | სამიზნე ფასი: ${ord.target_price:,.2f} | "
                        f"სტატუსი: {ord.status}"
                    )

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
