from sqlalchemy.orm import Session
from infrastructure.persistence.repositories.user_repository import UserRepository
from infrastructure.security.security import hash_password, verify_password
from core.result import Result
from domain.aggregates.user import User


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def login(self, username: str, password: str) -> Result[User, str]:
        user = self.user_repo.get_by_username(username)
        if not user:
            return Result.failure("მომხმარებელი ამ სახელით ვერ მოიძებნა.")

        if not verify_password(password, user.password_hash):
            return Result.failure("არასწორი პაროლი.")

        return Result.success(user)

    def register(
        self, username: str, raw_password: str, role=None
    ) -> Result[User, str]:
        existing_user = self.user_repo.get_by_username(username)

        if existing_user:
            return Result.failure("მომხმარებელი ამ სახელით უკვე არსებობს.")

        domain_result = User.create(username=username, password_hash="temporary_hash")

        if domain_result.is_failure:
            return Result.failure(domain_result.error)

        user = domain_result._value

        user.password_hash = hash_password(raw_password)
        if role:
            user.role = role

        saved_user = self.user_repo.save(user)

        return Result.success(saved_user)
