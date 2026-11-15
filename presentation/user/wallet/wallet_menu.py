from core.helpers import clear_console
from presentation.user.wallet.live_wallet_view import run_live_wallet_view
from presentation.user.wallet.deposit_menu import run_deposit_menu
from presentation.user.wallet.withdraw_menu import run_withdraw_menu
from presentation.user.wallet.transfer_menu import run_transfer_menu
from presentation.user.wallet.transactions_menu import run_transactions_menu
from presentation.user.wallet.portfolio_analytics_view import show_live_portfolio_analytics


def wallet_menu(user_id: int, username: str):
    user_id = int(user_id)
    while True:
        clear_console()
        print(f"\n--- ჩემი საფულე ({username}) ---")
        print("1. ბალანსისა და აქტივების ნახვა (LIVE სტრიმი)")
        print("2. დეპოზიტი (თანხის შეტანა)")
        print("3. თანხის გატანა (Withdrawal)")
        print("4. შიდა P2P გადარიცხვა (USD / კრიპტო)")
        print("5. ტრანზაქციების ისტორია & CSV ექსპორტი")
        print("6. პორტფოლიოს განაწილება & ანალიტიკა (LIVE)")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            clear_console()
            run_live_wallet_view(user_id=user_id, username=username)
            clear_console()

        elif choice == "2":
            run_deposit_menu(user_id=user_id)

        elif choice == "3":
            run_withdraw_menu(user_id=user_id)

        elif choice == "4":
            run_transfer_menu(user_id=user_id)

        elif choice == "5":
            run_transactions_menu(user_id=user_id)

        elif choice == "6":
            clear_console()
            show_live_portfolio_analytics(user_id=user_id)
            clear_console()

        elif choice == "0":
            clear_console()
            break
        else:
            clear_console()
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
