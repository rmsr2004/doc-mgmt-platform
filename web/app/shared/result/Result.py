from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

@dataclass
class Error:
    message: str

@dataclass(frozen=True)
class Result(Generic[T]):
    success: bool
    value: Optional[T] = None
    error: Optional[Error] = None

    def is_failure(self) -> bool:
        return not self.success

    @staticmethod
    def ok(value: T) -> "Result[T]":
        return Result(success=True, value=value, error=None)

    @staticmethod
    def fail(error: Error) -> "Result[T]":
        return Result(success=False, value=None, error=error)