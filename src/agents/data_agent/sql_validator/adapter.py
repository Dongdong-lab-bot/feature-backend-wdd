"""适配器：将业务安全校验注册到基建组 SQLGuard。

规范依据：docs/任务分配.md §模块三（三层校验边界）
- 数据组负责业务规则（我们），基建组负责全局兜底
- 通过 SQLGuard.custom_validators 插槽对接
"""

import sqlglot.expressions as exp

from src.core.exceptions import SQLSecurityBlockedError

from .security_check import check_sql_security


def wrap_security_check(ast: exp.Expression) -> tuple[bool, str]:
    """安全校验 → SQLGuard 自定义校验器格式。

    Args:
        ast: sqlglot 解析后的 AST

    Returns:
        (True, "")     → 通过
        (False, 原因)  → 拦截
    """
    sql = ast.sql(dialect="mysql")
    try:
        check_sql_security(sql)
        return True, ""
    except SQLSecurityBlockedError as exc:
        return False, exc.message
