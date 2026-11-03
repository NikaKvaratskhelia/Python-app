from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime
from datetime import datetime
from core.database import Base
from domain.aggregates.user import UserRole


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.REGULAR, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
