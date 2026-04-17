from __future__ import annotations


class DeviceDomainException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class LedgerBackfillError(DeviceDomainException):
    pass


class AlertDispatchError(DeviceDomainException):
    pass


__all__ = ["DeviceDomainException", "LedgerBackfillError", "AlertDispatchError"]
