from rich.console import Console
from infrastructure.security.session_storage import clear_session
from core.helpers import clear_console
from presentation.admin.users.users_menu import run_admin_users_menu
from presentation.admin.analytics.platform_stats_view import view_platform_stats_view
from presentation.admin.transactions.global_transactions_view import view_global_transactions_view
from presentation.admin.bot.bot_control_view import run_bot_control_view

console = Console()


def run_admin_menu(session_data: dict):
    admin_user_id = session_data.get("user_id")

    while True:
        clear_console()
        console.print(f"[bold magenta]=== ადმინისტრატორის მართვის პანელი ({session_data.get('username')}) ===[/bold magenta]\n")
        console.print("1. მომხმარებლების მართვა (სია, როლები, ბალანსის კორექტირება)")
        console.print("2. პლატფორმის გლობალური სტატისტიკა და ანალიტიკა")
        console.print("3. სისტემური ტრანზაქციების ჟურნალი (Audit Log)")
        console.print("4. სავაჭრო ბოტის მართვა და მონიტორინგი")
        console.print("5. სისტემიდან გამოსვლა (Logout)")
        console.print("0. აპლიკაციიდან გასვლა (Exit)")

        choice = input("\nაირჩიე (0-5): ").strip()

        if choice == "1":
            run_admin_users_menu(admin_user_id)
        elif choice == "2":
            view_platform_stats_view()
        elif choice == "3":
            view_global_transactions_view()
        elif choice == "4":
            run_bot_control_view()
        elif choice == "5":
            clear_console()
            clear_session()
            console.print("[green]გამოხვედით სისტემიდან.[/green]")
            return "logout"
        elif choice == "0":
            clear_console()
            console.print("[cyan]ნახვამდის![/cyan]")
            return "exit"
        else:
            console.print("[red]არასწორი არჩევანი.[/red]")
