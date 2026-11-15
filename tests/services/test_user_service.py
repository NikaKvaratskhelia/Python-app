from decimal import Decimal
from domain.aggregates.user.entities.user import User
from infrastructure.persistence.models.order_model import OrderModel
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.repositories.user_repository import UserRepository
from infrastructure.security.security import hash_password, verify_password
from services.user_service import UserService
from services.wallet_service import WalletService


def _setup_user_with_wallet(db_session, username="profile_user", initial_fiat=Decimal("5000.00")):
    user_repo = UserRepository(db_session)
    user = User(username=username, password_hash=hash_password("OldPass123!"))
    user_repo.save(user)
    db_session.commit()
    user_model = db_session.query(UserModel).filter(UserModel.username == username).first()

    wallet_model = WalletModel(user_id=user_model.id, fiat_balance=initial_fiat)
    db_session.add(wallet_model)
    db_session.commit()
    return user_model, wallet_model


def test_get_profile(db_session):
    user, _ = _setup_user_with_wallet(db_session, "profile_getter")
    user_svc = UserService(db_session)

    res = user_svc.get_profile(user.id)
    assert res.is_success
    data = res.value
    assert data["id"] == user.id
    assert data["username"] == "profile_getter"
    assert data["role"] == "regular"


def test_get_account_stats(db_session):
    user, wallet = _setup_user_with_wallet(db_session, "stats_user", Decimal("2000.00"))
    wallet_svc = WalletService(db_session)

    # 1 deposit
    wallet_svc.deposit(user.id, Decimal("500.00"))
    # 1 trade
    wallet_svc.buy_asset(user.id, "BTC", Decimal("0.01"), Decimal("50000.00"))
    db_session.commit()

    # 1 active order
    order = OrderModel(
        wallet_id=wallet.id,
        symbol="ETH",
        order_type="BUY_LIMIT",
        target_price=Decimal("2000.00"),
        amount=Decimal("0.5"),
        status="PENDING",
    )
    db_session.add(order)
    db_session.commit()

    user_svc = UserService(db_session)
    res = user_svc.get_account_stats(user.id)
    assert res.is_success
    stats = res.value
    assert stats["total_transactions"] >= 2
    assert stats["trades_count"] >= 1
    assert stats["active_orders"] == 1
    assert stats["holding_assets_count"] == 1


def test_change_password_success(db_session):
    user, _ = _setup_user_with_wallet(db_session, "pw_changer")
    user_svc = UserService(db_session)

    res = user_svc.change_password(user.id, "OldPass123!", "NewSecret456@")
    assert res.is_success

    db_session.refresh(user)
    assert verify_password("NewSecret456@", user.password_hash)
    assert not verify_password("OldPass123!", user.password_hash)


def test_change_password_wrong_current(db_session):
    user, _ = _setup_user_with_wallet(db_session, "wrong_pw_user")
    user_svc = UserService(db_session)

    res = user_svc.change_password(user.id, "WrongOldPass!", "NewSecret456@")
    assert res.is_failure
    assert "მიმდინარე პაროლი არასწორია" in res.error


def test_change_password_same_as_old(db_session):
    user, _ = _setup_user_with_wallet(db_session, "same_pw_user")
    user_svc = UserService(db_session)

    res = user_svc.change_password(user.id, "OldPass123!", "OldPass123!")
    assert res.is_failure
    assert "არ შეიძლება ემთხვეოდეს" in res.error


def test_change_password_weak_new(db_session):
    user, _ = _setup_user_with_wallet(db_session, "weak_pw_user")
    user_svc = UserService(db_session)

    res = user_svc.change_password(user.id, "OldPass123!", "weak")
    assert res.is_failure
    assert "მინიმუმ 8 სიმბოლო" in res.error


def test_change_username_success(db_session):
    user, _ = _setup_user_with_wallet(db_session, "old_name_user")
    user_svc = UserService(db_session)

    res = user_svc.change_username(user.id, "new_cool_name")
    assert res.is_success
    assert res.value == "new_cool_name"

    db_session.refresh(user)
    assert user.username == "new_cool_name"


def test_change_username_already_taken(db_session):
    user1, _ = _setup_user_with_wallet(db_session, "first_user")
    user2, _ = _setup_user_with_wallet(db_session, "second_user")

    user_svc = UserService(db_session)
    res = user_svc.change_username(user2.id, "first_user")
    assert res.is_failure
    assert "უკვე არსებობს" in res.error


def test_change_username_too_short(db_session):
    user, _ = _setup_user_with_wallet(db_session, "short_user")
    user_svc = UserService(db_session)

    res = user_svc.change_username(user.id, "ab")
    assert res.is_failure
    assert "მინიმუმ 3" in res.error
