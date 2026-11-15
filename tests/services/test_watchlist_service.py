from domain.aggregates.user.entities.user import User
from infrastructure.persistence.repositories.user_repository import UserRepository
from services.watchlist_service import WatchlistService


def _create_user(db_session, username="watch_user"):
    repo = UserRepository(db_session)
    user = User(username=username, password_hash="hash")
    repo.save(user)
    db_session.commit()
    return repo.get_by_username(username).id


def test_watchlist_add_and_get(db_session):
    user_id = _create_user(db_session, "user_w1")
    service = WatchlistService(db_session)

    res1 = service.add(user_id, "BTC")
    assert res1.is_success
    res2 = service.add(user_id, "ETH")
    assert res2.is_success

    items = service.get_watchlist(user_id)
    assert items == ["BTC", "ETH"]


def test_watchlist_duplicate_prevention(db_session):
    user_id = _create_user(db_session, "user_w2")
    service = WatchlistService(db_session)

    assert service.add(user_id, "SOL").is_success
    dup_res = service.add(user_id, "SOL")
    assert dup_res.is_failure
    assert "უკვე დამატებულია" in dup_res.error


def test_watchlist_remove(db_session):
    user_id = _create_user(db_session, "user_w3")
    service = WatchlistService(db_session)

    service.add(user_id, "AVAX")
    service.add(user_id, "DOT")

    del_res = service.remove(user_id, "AVAX")
    assert del_res.is_success

    remaining = service.get_watchlist(user_id)
    assert remaining == ["DOT"]

    bad_del = service.remove(user_id, "BTC")
    assert bad_del.is_failure
    assert "ვერ მოიძებნა" in bad_del.error
