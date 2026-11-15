from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import contextmanager
from core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@contextmanager
def get_db(session: Optional[Session] = None):
    if session is not None:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
    else:
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
