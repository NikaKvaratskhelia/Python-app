from typing import Generic, TypeVar, Optional, Callable, Any
from dataclasses import dataclass

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True)
class Result(Generic[T, E]):
    _value: Optional[T] = None
    _error: Optional[E] = None
    is_success: bool = True

    @property
    def is_failure(self) -> bool:
        return not self.is_success

    @staticmethod
    def success(value: T) -> "Result[T, Any]":
        return Result(_value=value, _error=None, is_success=True)

    @staticmethod
    def failure(error: E) -> "Result[Any, E]":
        return Result(_value=None, _error=error, is_success=False)

    def match(self, on_success: Callable[[T], U], on_failure: Callable[[E], U]) -> U:
        if self.is_success:
            return on_success(self._value)
        return on_failure(self._error)

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        if self.is_failure:
            return self
        return Result.success(func(self._value))

    def bind(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        if self.is_failure:
            return self
        return func(self._value)

    def tap(self, func: Callable[[T], Any]) -> "Result[T, E]":
        if self.is_success:
            func(self._value)
        return self

    def ensure(self, predicate: Callable[[T], bool], error: E) -> "Result[T, E]":
        if self.is_failure:
            return self
        if predicate(self._value):
            return self
        return Result.failure(error)

    def ensure_found(self, error: E) -> "Result[T, E]":
        if self.is_failure:
            return self
        if self._value is not None:
            return self
        return Result.failure(error)
