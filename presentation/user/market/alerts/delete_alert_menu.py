from rich.console import Console
from core.database import get_db
from core.result import Result
from services.alert_service import AlertService

console = Console()


def run_delete_alert_menu(user_id: int):
    alert_id_str = input("შეიყვანეთ წასაშლელი შეტყობინების ID: ").strip()
    id_res = Result.try_catch(lambda: int(alert_id_str), lambda _: "ID უნდა იყოს რიცხვი.")
    if id_res.is_failure:
        console.print(f"[red]შეცდომა: {id_res.error}[/red]")
        return

    with get_db() as db:
        alert_svc = AlertService(db)
        del_res = alert_svc.delete_alert(id_res.value, user_id)

    if del_res.is_success:
        console.print("[green]შეტყობინება წარმატებით წაიშალა.[/green]")
    else:
        console.print(f"[red]შეცდომა: {del_res.error}[/red]")
