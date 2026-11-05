import re

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

    @staticmethod
    def validate_username(username: str) -> Result[str, str]:

        if len(username) < 3:
            return Result.failure("იუზერნეიმი უნდა შედგებოდეს მინიმუმ 3 სიმბოლოსგან.")

        return Result.success(username)

    @staticmethod
    def validate_password(password: str) -> Result[str, str]:
        pattern = (
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        )
        
        if not re.match(pattern, password):
            return Result.failure(
                "პაროლი უნდა იყოს მინიმუმ 8 სიმბოლო და შეიცავდეს:\n"
                "   - მინიმუმ ერთ დიდ ასოს (A-Z)\n"
                "   - მინიმუმ ერთ პატარა ასოს (a-z)\n"
                "   - მინიმუმ ერთ ციფრს (0-9)\n"
                "   - მინიმუმ ერთ სპეციალურ სიმბოლოს (@$!%*?&)"
            )
            
        return Result.success(password)
