from decimal import Decimal
from domain.aggregates.user.entities.user import User
from domain.aggregates.user.enums.user_role import UserRole
from domain.aggregates.wallet.entities.wallet import Wallet
from infrastructure.persistence.repositories.user_repository import UserRepository
from infrastructure.persistence.repositories.wallet_repository import WalletRepository


def test_user_repository_save_and_get(db_session):
    repo = UserRepository(db_session)

    user = User(
        username="charlie",
        password_hash="some_hashed_val",
        role=UserRole.REGULAR,
    )
    repo.save(user)
    db_session.commit()

    retrieved = repo.get_by_username("charlie")
    assert retrieved is not None
    assert retrieved.username == "charlie"
    assert retrieved.password_hash == "some_hashed_val"
    assert retrieved.role == UserRole.REGULAR

    not_found = repo.get_by_username("non_existent")
    assert not_found is None


def test_wallet_repository_save_and_get(db_session):
    user_repo = UserRepository(db_session)
    user = User(username="wallet_user", password_hash="hash")
    user_repo.save(user)
    db_session.commit()

    saved_user = user_repo.get_by_username("wallet_user")

    wallet_repo = WalletRepository(db_session)
    wallet = Wallet(
        id=None,
        user_id=saved_user.id,
        fiat_balance=Decimal("2500.50"),
    )
    saved_wallet = wallet_repo.save(wallet)
    db_session.commit()

    assert saved_wallet.fiat_balance == Decimal("2500.50")
    assert saved_wallet.user_id == saved_user.id

    # Retrieve wallet
    fetched = wallet_repo.get_by_user_id(saved_user.id)
    assert fetched is not None
    assert fetched.fiat_balance == Decimal("2500.50")

    # Update balance
    fetched.fiat_balance = Decimal("3000.00")
    wallet_repo.save(fetched)
    db_session.commit()

    updated = wallet_repo.get_by_user_id(saved_user.id)
    assert updated.fiat_balance == Decimal("3000.00")
