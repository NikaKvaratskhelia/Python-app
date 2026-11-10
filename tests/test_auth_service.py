from services.auth_service import AuthService
from domain.aggregates.user.enums.user_role import UserRole


def test_auth_service_register_success(db_session):
    service = AuthService(db_session)
    res = service.register(username="validuser", raw_password="ValidPassword1!")
    db_session.commit()

    assert res.is_success is True
    user = res.value
    assert user.username == "validuser"
    assert user.role == UserRole.REGULAR


def test_auth_service_register_duplicate(db_session):
    service = AuthService(db_session)
    res1 = service.register(username="sameuser", raw_password="ValidPassword1!")
    assert res1.is_success is True
    db_session.commit()

    res2 = service.register(username="sameuser", raw_password="ValidPassword1!")
    assert res2.is_failure is True
    assert "უკვე არსებობს" in res2.error


def test_auth_service_register_invalid_domain_username(db_session):
    service = AuthService(db_session)
    res = service.register(username="a", raw_password="ValidPassword1!")
    assert res.is_failure is True
    assert "მინიმუმ 3 სიმბოლოსგან" in res.error


def test_auth_service_login_success(db_session):
    service = AuthService(db_session)
    service.register(username="loginuser", raw_password="CorrectPassword1!")
    db_session.commit()

    login_res = service.login("loginuser", "CorrectPassword1!")
    assert login_res.is_success is True
    assert login_res.value.username == "loginuser"


def test_auth_service_login_wrong_password(db_session):
    service = AuthService(db_session)
    service.register(username="wrongpassuser", raw_password="CorrectPassword1!")
    db_session.commit()

    login_res = service.login("wrongpassuser", "WrongPassword1!")
    assert login_res.is_failure is True
    assert "არასწორი პაროლი" in login_res.error


def test_auth_service_login_non_existent_user(db_session):
    service = AuthService(db_session)
    login_res = service.login("ghost_user", "AnyPassword1!")
    assert login_res.is_failure is True
    assert "ვერ მოიძებნა" in login_res.error
