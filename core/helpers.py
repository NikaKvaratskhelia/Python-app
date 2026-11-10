import os
import subprocess
import termios
import tty
import sys


def clear_console():
    subprocess.run(["cls" if os.name == "nt" else "clear"], shell=True)


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
