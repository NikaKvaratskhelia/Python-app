from rich.console import Console
from core.helpers import clear_console
from presentation.admin.users.view_users_view import view_all_users_view
from presentation.admin.users.change_role_menu import run_change_role_menu
from presentation.admin.users.adjust_balance_menu import run_adjust_balance_menu

console = Console()


def run_admin_users_menu(admin_user_id: int):
    while True:
        clear_console()
        console.print("[bold cyan]=== მომხმარებლების მართვის მენიუ ===[/bold cyan]\n")
        console.print("1. ყველა მომხმარებლის სია და ბალანსები")
        console.print("2. მომხმარებლის როლის შეცვლა (ADMIN / REGULAR)")
        console.print("3. მომხმარებლის ბალანსის კორექტირება (დარიცხვა / ჩამოჭრა)")
        console.print("0. უკან დაბრუნება")

        choice = input("\nაირჩიეთ: ").strip()

        if choice == "1":
            view_all_users_view()
        elif choice == "2":
            run_change_role_menu(admin_user_id)
        elif choice == "3":
            run_adjust_balance_menu(admin_user_id)
        elif choice == "0":
            break
        else:
            console.print("[red]არასწორი არჩევანი.[/red]")
