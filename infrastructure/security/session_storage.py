import json
from pathlib import Path
from infrastructure.security.jwt_manager import decode_access_token

SESSION_FILE = Path(".session.json")


def save_session(session_data: dict):
    SESSION_FILE.write_text(json.dumps(session_data, indent=4))


def get_session() -> dict | None:
    if not SESSION_FILE.exists():
        return None

    try:
        data = json.loads(SESSION_FILE.read_text())
        token = data.get("access_token")

        if not token:
            return None

        payload = decode_access_token(token)
        if not payload:
            clear_session()
            return None

        return {
            "access_token": token,
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
        }

    except (json.JSONDecodeError, Exception):
        clear_session()
        return None


def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
