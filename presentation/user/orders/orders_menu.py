from core.helpers import clear_console
from presentation.user.orders.view_orders_menu import run_view_orders_menu
from presentation.user.orders.create_order_menu import run_create_order_menu
from presentation.user.orders.cancel_order_menu import run_cancel_order_menu


def order_menu(user_id: int, username: str):
    user_id = int(user_id)

    while True:
        clear_console()
        print(f"\n--- ორდერების მართვა და ვაჭრობა ({username}) ---")

        print("1. ორდერების ნახვა (LIVE ბაზრის მონიტორინგი)")
        print("2. ახალი ორდერის შექმნა")
        print("3. ორდერის გაუქმება (Cancel Order)")
        print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ მოქმედება: ").strip()

        if choice == "1":
            run_view_orders_menu(user_id=user_id)

        elif choice == "2":
            run_create_order_menu(user_id=user_id)

        elif choice == "3":
            run_cancel_order_menu(user_id=user_id)

        elif choice == "0":
            clear_console()
            break
        else:
            clear_console()
            print("არასწორი არჩევანი, სცადეთ თავიდან.")
