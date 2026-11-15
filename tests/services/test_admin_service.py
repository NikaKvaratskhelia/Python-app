from decimal import Decimal
import pytest
from core.database import get_db
from domain.aggregates.user.enums.user_role import UserRole
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.security.security import hash_password
from services.admin_service import AdminService


def _setup_test_data(db_session):
    admin = UserModel(
        username="admin_user",
        password_hash=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
    )
    user = UserModel(
        username="reg_user",
        password_hash=hash_password("UserPass123!"),
        role=UserRole.REGULAR,
    )
    db_session.add(admin)
    db_session.add(user)
    db_session.commit()

    admin_wallet = WalletModel(user_id=admin.id, fiat_balance=Decimal("1000.00"))
    user_wallet = WalletModel(user_id=user.id, fiat_balance=Decimal("500.00"))
    db_session.add(admin_wallet)
    db_session.add(user_wallet)
    db_session.commit()

    tx = TransactionModel(
        wallet_id=user_wallet.id,
        type="DEPOSIT",
        amount=Decimal("500.00"),
        price=Decimal("1.00"),
        symbol="USD",
    )
    db_session.add(tx)
    db_session.commit()

    return admin, user


def test_get_all_users(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    users = service.get_all_users()
    assert len(users) >= 2
    usernames = [u["username"] for u in users]
    assert "admin_user" in usernames
    assert "reg_user" in usernames

    user_info = next(u for u in users if u["username"] == "reg_user")
    assert user_info["fiat_balance"] == Decimal("500.00")
    assert user_info["role"] == "regular"


def test_change_user_role_success(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    res = service.change_user_role(
        target_user_id=user.id, new_role="ADMIN", admin_user_id=admin.id
    )
    assert res.is_success

    db_session.refresh(user)
    assert user.role == UserRole.ADMIN


def test_change_user_role_cannot_demote_self(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    res = service.change_user_role(
        target_user_id=admin.id, new_role="REGULAR", admin_user_id=admin.id
    )
    assert res.is_failure
    assert "საკუთარ როლს ვერ შეიცვლით" in res.error


def test_change_user_role_already_has_role(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    res = service.change_user_role(
        target_user_id=user.id, new_role="REGULAR", admin_user_id=admin.id
    )
    assert res.is_failure
    assert "უკვე აქვს როლი" in res.error


def test_adjust_user_balance_credit(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    res = service.adjust_user_balance(
        target_user_id=user.id, amount=Decimal("250.00"), admin_user_id=admin.id
    )
    assert res.is_success
    assert res.value == Decimal("750.00")

    wallet = db_session.query(WalletModel).filter(WalletModel.user_id == user.id).first()
    db_session.refresh(wallet)
    assert wallet.fiat_balance == Decimal("750.00")


def test_adjust_user_balance_debit(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    res = service.adjust_user_balance(
        target_user_id=user.id, amount=Decimal("-200.00"), admin_user_id=admin.id
    )
    assert res.is_success
    assert res.value == Decimal("300.00")


def test_adjust_user_balance_insufficient(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    res = service.adjust_user_balance(
        target_user_id=user.id, amount=Decimal("-1000.00"), admin_user_id=admin.id
    )
    assert res.is_failure
    assert "არასაკმარისი ბალანსი" in res.error


def test_get_platform_stats(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    stats = service.get_platform_stats()
    assert stats["total_users"] >= 2
    assert stats["total_fiat_liquidity"] >= Decimal("1500.00")
    assert stats["total_transactions"] >= 1


def test_get_global_transactions(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    txs = service.get_global_transactions(limit=10)
    assert len(txs) >= 1
    assert txs[0]["username"] == "reg_user"
    assert txs[0]["symbol"] == "USD"
    assert txs[0]["amount"] == Decimal("500.00")


def test_get_bot_status_and_force_run(db_session):
    admin, user = _setup_test_data(db_session)
    service = AdminService(db_session)

    status = service.get_bot_status()
    assert "pending_orders" in status
    assert "active_alerts" in status

    # Force run check should not raise any error
    service.force_run_bot_cycle()
