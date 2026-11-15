from unittest.mock import MagicMock
from core.database import get_db


def test_get_db_success(monkeypatch):
    mock_session = MagicMock()
    monkeypatch.setattr("core.database.SessionLocal", lambda: mock_session)

    with get_db() as db:
        assert db is mock_session

    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()
    mock_session.rollback.assert_not_called()


def test_get_db_rollback_without_raise(monkeypatch):
    mock_session = MagicMock()
    mock_session.commit.side_effect = Exception("DB error")
    monkeypatch.setattr("core.database.SessionLocal", lambda: mock_session)

    # Should not raise any exception
    with get_db() as db:
        pass

    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()
