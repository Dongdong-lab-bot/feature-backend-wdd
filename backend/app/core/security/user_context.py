"""仅用于兼容旧版导入路径的占位模块。"""
from __future__ import annotations

import warnings

from app.core.context import (
    TenantContextMissing,
    UserContext,
    role_var,
    scope_var,
    tenant_var,
    user_var,
)

warnings.warn(
    "app.core.security.user_context 已弃用，请改用 app.core.context.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "TenantContextMissing",
    "UserContext",
    "user_var",
    "tenant_var",
    "role_var",
    "scope_var",
]
