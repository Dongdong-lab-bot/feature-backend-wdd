"""Ledger 表单自动填充的上下文辅助。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


AUTO_FILL_CURRENT_TIME = "current_time"
AUTO_FILL_CANTEEN_NAME = "canteen_name"
AUTO_FILL_USER_NAME = "user_name"


def get_auto_fill_value(auto_fill: str, context: Dict[str, Any]) -> Any:
    """返回指定类型的自动填充值。

    Args:
        auto_fill: auto_fill 类型。
        context: 提供的上下文数据。

    Returns:
        需要注入表单的数据。

    Raises:
        KeyError: 缺少必要的上下文键时抛出。
        ValueError: 遇到不支持的 auto_fill 类型时抛出。
    """
    if auto_fill == AUTO_FILL_CURRENT_TIME:
        return datetime.now().isoformat()
    if auto_fill == AUTO_FILL_CANTEEN_NAME:
        return context[AUTO_FILL_CANTEEN_NAME]
    if auto_fill == AUTO_FILL_USER_NAME:
        return context[AUTO_FILL_USER_NAME]
    raise ValueError(f"unsupported auto_fill: {auto_fill}")


def build_auto_fill_context(
    *,
    canteen_name: Optional[str] = None,
    user_name: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """构建标准化的自动填充上下文字典。"""

    context: Dict[str, Any] = dict(extra or {})
    if canteen_name is not None:
        context[AUTO_FILL_CANTEEN_NAME] = canteen_name
    if user_name is not None:
        context[AUTO_FILL_USER_NAME] = user_name
    return context
