from decimal import Decimal
from domain.aggregates.user.entities.user import User
from infrastructure.persistence.repositories.user_repository import UserRepository
from services.alert_service import AlertService


def _create_user(db_session, username="alert_user"):
    repo = UserRepository(db_session)
    user = User(username=username, password_hash="hash")
    repo.save(user)
    db_session.commit()
    return repo.get_by_username(username).id


def test_create_and_get_alerts(db_session):
    user_id = _create_user(db_session, "user_a1")
    service = AlertService(db_session)

    res = service.create_alert(user_id, "BTC", Decimal("95000.00"), "ABOVE")
    assert res.is_success
    alert = res.value
    assert alert.symbol == "BTC"
    assert alert.condition == "ABOVE"
    assert alert.is_triggered is False

    alerts = service.get_user_alerts(user_id)
    assert len(alerts) == 1


def test_check_and_trigger_alerts(db_session):
    user_id = _create_user(db_session, "user_a2")
    service = AlertService(db_session)

    # 1 alert when ETH > 3000
    service.create_alert(user_id, "ETH", Decimal("3000.00"), "ABOVE")
    # 1 alert when SOL < 150
    service.create_alert(user_id, "SOL", Decimal("150.00"), "BELOW")

    prices = {
        "ETH": {"price": Decimal("3100.00")},  # Should trigger ABOVE
        "SOL": {"price": Decimal("180.00")},   # Should NOT trigger BELOW
    }

    triggered = AlertService.check_and_trigger_alerts(db_session, prices)
    assert len(triggered) == 1
    assert triggered[0].symbol == "ETH"
    assert triggered[0].is_triggered is True

    # Active alerts remaining: only SOL
    active = service.get_user_alerts(user_id, active_only=True)
    assert len(active) == 1
    assert active[0].symbol == "SOL"


def test_delete_alert(db_session):
    user_id = _create_user(db_session, "user_a3")
    service = AlertService(db_session)

    res = service.create_alert(user_id, "DOGE", Decimal("0.40"), "ABOVE")
    alert_id = res.value.id

    del_res = service.delete_alert(alert_id, user_id)
    assert del_res.is_success

    alerts = service.get_user_alerts(user_id, active_only=False)
    assert len(alerts) == 0
