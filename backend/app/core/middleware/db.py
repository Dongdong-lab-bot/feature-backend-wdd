"""已废弃的同步数据库中间件，仅用于提醒旧代码迁移。

FastAPI 现通过 ``app.db.session.get_db`` 获取 AsyncSession，因此该模块若被引用，说明
仍有遗留代码尚未升级，需要尽快移除中间件写法。
"""

import warnings

warnings.warn(
    "DBSessionMiddleware 已弃用，请删除 app.core.middleware.db 引用，改用 get_db 依赖注入。",
    DeprecationWarning,
    stacklevel=2,
)


class DBSessionMiddleware:  # pragma: no cover
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "DBSessionMiddleware 已被移除，请使用 async get_db 依赖，而非中间件。"
        )


__all__ = ["DBSessionMiddleware"]
