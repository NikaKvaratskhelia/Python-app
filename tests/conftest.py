import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
import infrastructure.persistence.models.user_model
import infrastructure.persistence.models.wallet_model
import infrastructure.persistence.models.wallet_asset
import infrastructure.persistence.models.transaction_model


@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database session for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)
