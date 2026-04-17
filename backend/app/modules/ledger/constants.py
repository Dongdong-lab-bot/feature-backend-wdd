"""Ledger module constants and status machine definitions."""

from enum import Enum


class LedgerStatus(str, Enum):
    """台账实例状态机，参照《模块二契约》。"""

    PENDING = "PENDING"  # 待填报(系统生成)
    FILLING = "FILLING"  # 填报中(暂存)
    SIGNED = "SIGNED"  # 已签字(提交,不可改)
    ARCHIVED = "ARCHIVED"  # 已归档(历史数据)


ALLOWED_TRANSITIONS = {
    LedgerStatus.PENDING: [LedgerStatus.FILLING, LedgerStatus.SIGNED],
    LedgerStatus.FILLING: [LedgerStatus.SIGNED],
    LedgerStatus.SIGNED: [LedgerStatus.ARCHIVED],
    LedgerStatus.ARCHIVED: [],
}


__all__ = ["LedgerStatus", "ALLOWED_TRANSITIONS"]
