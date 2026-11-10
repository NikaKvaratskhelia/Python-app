from domain.aggregates.user.entities.user import User
from domain.aggregates.user.enums.user_role import UserRole
from domain.aggregates.user.validators.user_validators import UserValidator


def test_validate_username_success():
    res = UserValidator.validate_username("nika")
    assert res.is_success is True
    assert res.value == "nika"


def test_validate_username_too_short():
    res = UserValidator.validate_username("ab")
    assert res.is_failure is True
    assert "მინიმუმ 3 სიმბოლოსგან" in res.error


def test_validate_password_hash():
    valid = UserValidator.validate_password_hash("some_hashed_password")
    assert valid.is_success is True
    assert valid.value == "some_hashed_password"

    invalid = UserValidator.validate_password_hash("   ")
    assert invalid.is_failure is True
    assert "პაროლის ჰეში არ არის ვალიდური." in invalid.error


def test_validate_password():
    # Valid password: >= 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
    valid = UserValidator.validate_password("StrongP@ss1")
    assert valid.is_success is True
    assert valid.value == "StrongP@ss1"

    # Missing special character
    invalid1 = UserValidator.validate_password("StrongPass1")
    assert invalid1.is_failure is True

    # Too short
    invalid2 = UserValidator.validate_password("St1@p")
    assert invalid2.is_failure is True

    # Missing uppercase
    invalid3 = UserValidator.validate_password("weakp@ss1")
    assert invalid3.is_failure is True


def test_user_creation_success():
    result = User.create(
        username="john_doe",
        password_hash="hashed_secret",
        role=UserRole.REGULAR,
    )
    assert result.is_success is True
    user = result.value
    assert user.username == "john_doe"
    assert user.password_hash == "hashed_secret"
    assert user.role == UserRole.REGULAR
    assert user.is_admin() is False


def test_user_creation_failure_invalid_username():
    result = User.create(username="ab", password_hash="hashed_secret")
    assert result.is_failure is True
    assert "მინიმუმ 3 სიმბოლოსგან" in result.error


def test_user_creation_failure_invalid_password_hash():
    result = User.create(username="valid_user", password_hash="")
    assert result.is_failure is True
    assert "პაროლის ჰეში არ არის ვალიდური." in result.error


def test_user_admin_promotion():
    user = User.create(username="admin_user", password_hash="hash").value
    assert user.is_admin() is False
    user.promote_to_admin()
    assert user.is_admin() is True
    assert user.role == UserRole.ADMIN
