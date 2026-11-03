from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.result import Result
from domain.aggregates.user.enums.user_role import UserRole
from domain.aggregates.user.validators.user_validators import UserValidator


@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.REGULAR
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
        username: str,
        password_hash: str,
        role: UserRole = UserRole.REGULAR,
    ) -> Result["User", str]:
        username_result = UserValidator.validate_username(username)

        if username_result.is_failure:
            return Result.failure(username_result._error)

        password_result = UserValidator.validate_password_hash(password_hash)

        if password_result.is_failure:
            return Result.failure(password_result._error)

        user = User(
            username = username_result._value,
            password_hash = password_result._value,
            role = role,
        )
        return Result.success(user)

    def promote_to_admin(self) -> None:
        self.role = UserRole.ADMIN

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
