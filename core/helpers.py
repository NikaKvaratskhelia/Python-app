import io
import os
import select
import subprocess
import termios
import tty
import sys
from typing import Callable, Any
from rich.live import Live
from rich.console import Console


def clear_console():
    subprocess.run(["cls" if os.name == "nt" else "clear"], shell=True)


def run_live_loop(
    render_factory: Callable[[], Any],
    refresh_per_second: int = 2,
    console: Console | None = None,
    poll_timeout: float = 0.5,
    on_input: Callable[[str], Any] | None = None,
) -> Any:
    """Runs a Rich Live rendering loop until Enter or KeyboardInterrupt."""
    cons = console or Console()
    try:
        with Live(render_factory(), refresh_per_second=refresh_per_second, console=cons) as live:
            while True:
                live.update(render_factory())
                try:
                    rlist, _, _ = select.select([sys.stdin], [], [], poll_timeout)
                except (io.UnsupportedOperation, ValueError, OSError):
                    rlist = [sys.stdin]
                if rlist:
                    line = sys.stdin.readline()
                    if on_input:
                        return on_input(line)
                    break
    except KeyboardInterrupt:
        pass
    clear_console()
    return None


def get_masked_password(prompt="Password: "):
    sys.stdout.write(prompt)
    sys.stdout.flush()

    password = []

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            char = sys.stdin.read(1)

            if char in ("\n", "\r"):
                sys.stdout.write("\r\n")
                break

            elif ord(char) == 127 or ord(char) == 8:
                if password:
                    password.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ord(char) == 3:
                sys.stdout.write("\r\n")
                return ""
            else:
                password.append(char)
                sys.stdout.write("*")
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return "".join(password)
