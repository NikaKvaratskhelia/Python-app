from sqlalchemy.orm import Session
from infrastructure.persistence.models.user_model import UserModel
from domain.aggregates.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        model = self.db.query(UserModel).filter(UserModel.username == username).first()

        if not model:
            return None

        return User(
            id=model.id,
            username=model.username,
            password_hash=model.password_hash,
            role=model.role,
            created_at=model.created_at,
        )

    def save(self, user: User) -> User:
        model = UserModel(
            username=user.username,
            password_hash=user.password_hash,
            role=user.role,
            created_at=user.created_at,
        )
        
        self.db.add(model)
        return user
