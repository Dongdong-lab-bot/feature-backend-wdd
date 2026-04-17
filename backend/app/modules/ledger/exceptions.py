"""Ledger domain specific exception helpers."""
from __future__ import annotations


class FieldValidationError(ValueError):
    """Raised when ledger form data fails schema validation."""

    def __init__(self, field_id: str, message: str) -> None:
        self.field_id = field_id
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:  # pragma: no cover - inherited behavior is enough
        return self.message


__all__ = ["FieldValidationError"]
