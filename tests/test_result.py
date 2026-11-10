import pytest
from core.result import Result


def test_result_success():
    res = Result.success(100)
    assert res.is_success is True
    assert res.is_failure is False
    assert res.value == 100
    assert res.error is None


def test_result_failure():
    res = Result.failure("error occurred")
    assert res.is_success is False
    assert res.is_failure is True
    assert res.value is None
    assert res.error == "error occurred"


def test_result_match():
    success_res = Result.success("ok")
    matched_s = success_res.match(
        on_success=lambda v: f"Value: {v}",
        on_failure=lambda e: f"Error: {e}",
    )
    assert matched_s == "Value: ok"

    failure_res = Result.failure("err")
    matched_f = failure_res.match(
        on_success=lambda v: f"Value: {v}",
        on_failure=lambda e: f"Error: {e}",
    )
    assert matched_f == "Error: err"


def test_result_map():
    res = Result.success(5).map(lambda x: x * 2)
    assert res.is_success is True
    assert res.value == 10

    fail = Result.failure("failed").map(lambda x: x * 2)
    assert fail.is_failure is True
    assert fail.error == "failed"


def test_result_bind():
    def double_if_even(x: int):
        if x % 2 == 0:
            return Result.success(x * 2)
        return Result.failure("not even")

    res1 = Result.success(4).bind(double_if_even)
    assert res1.is_success is True
    assert res1.value == 8

    res2 = Result.success(3).bind(double_if_even)
    assert res2.is_failure is True
    assert res2.error == "not even"

    res3 = Result.failure("original error").bind(double_if_even)
    assert res3.is_failure is True
    assert res3.error == "original error"


def test_result_tap():
    side_effects = []
    res = Result.success("item").tap(lambda v: side_effects.append(v))
    assert res.value == "item"
    assert side_effects == ["item"]

    fail = Result.failure("item_fail").tap(lambda v: side_effects.append(v))
    assert fail.error == "item_fail"
    assert side_effects == ["item"]


def test_result_ensure():
    res1 = Result.success(10).ensure(lambda x: x > 5, "must be greater than 5")
    assert res1.is_success is True
    assert res1.value == 10

    res2 = Result.success(3).ensure(lambda x: x > 5, "must be greater than 5")
    assert res2.is_failure is True
    assert res2.error == "must be greater than 5"

    res3 = Result.failure("prior err").ensure(lambda x: x > 5, "must be greater than 5")
    assert res3.is_failure is True
    assert res3.error == "prior err"


def test_result_ensure_found():
    res1 = Result.success("found").ensure_found("not found")
    assert res1.is_success is True
    assert res1.value == "found"

    res2 = Result.success(None).ensure_found("not found")
    assert res2.is_failure is True
    assert res2.error == "not found"


def test_result_try_catch():
    success = Result.try_catch(lambda: int("123"))
    assert success.is_success is True
    assert success.value == 123

    failure = Result.try_catch(lambda: int("abc"), error_mapper=lambda e: "invalid int")
    assert failure.is_failure is True
    assert failure.error == "invalid int"

    default_failure = Result.try_catch(lambda: int("xyz"))
    assert default_failure.is_failure is True
    assert "invalid literal for int()" in default_failure.error
