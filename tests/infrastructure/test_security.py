from infrastructure.security.security import hash_password, verify_password
from infrastructure.security.jwt_manager import create_access_token, decode_access_token
from infrastructure.security import session_storage


def test_password_hashing_and_verification():
    raw = "MyP@ssw0rd!"
    hashed = hash_password(raw)

    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_create_and_decode():
    token = create_access_token(user_id=42, username="test_user", role="admin")
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["username"] == "test_user"
    assert payload["role"] == "admin"


def test_jwt_decode_invalid():
    invalid_token = "invalid.token.string"
    assert decode_access_token(invalid_token) is None


def test_session_lifecycle(tmp_path, monkeypatch):
    test_session_file = tmp_path / ".test_session.json"
    monkeypatch.setattr(session_storage, "SESSION_FILE", test_session_file)

    # Initial state: no session
    assert session_storage.get_session() is None

    # Save session
    token = create_access_token(user_id=1, username="alice", role="regular")
    session_storage.save_session({"access_token": token})

    # Retrieve session
    session = session_storage.get_session()
    assert session is not None
    assert session["user_id"] == "1"
    assert session["username"] == "alice"
    assert session["role"] == "regular"

    # Clear session
    session_storage.clear_session()
    assert session_storage.get_session() is None
    assert not test_session_file.exists()
