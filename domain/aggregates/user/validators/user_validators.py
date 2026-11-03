from pydantic import TypeAdapter, ValidationError, StringConstraints
from typing_extensions import Annotated
from core.result import Result


class UserValidator:
    _username_adapter = TypeAdapter(
        Annotated[str, StringConstraints(min_length=3, strip_whitespace=True)]
    )

    @staticmethod
    def validate_username(username: str) -> Result[str, str]:
        if not username or not username.strip():
            return Result.failure("მომხმარებლის სახელი არ შეიძლება იყოს ცარიელი.")

        try:
            validated = UserValidator._username_adapter.validate_python(username)
            return Result.success(validated)
        except ValidationError:
            return Result.failure(
                "მომხმარებლის სახელი უნდა შედგებოდეს მინიმუმ 3 სიმბოლოსგან."
            )

    @staticmethod
    def validate_password_hash(password_hash: str) -> Result[str, str]:
        if not password_hash or not password_hash.strip():
            return Result.failure("პაროლის ჰეში არ არის ვალიდური.")

        return Result.success(password_hash.strip())
