"""
SQL 安全校验模块（柴文烨 / 安全红线防御）

拦截规则（纯语法层面，与表名无关）：
  RULE-S001  多语句        — 每次请求只允许单条 SQL
  RULE-S002  写操作 (DML)  — 禁止 INSERT / UPDATE / DELETE / MERGE
  RULE-S003  DDL           — 禁止 CREATE / DROP / ALTER / TRUNCATE
  RULE-S004  存储过程/命令 — 禁止 CALL 及 sqlglot 无法识别的原始命令（exp.Command）
  RULE-S005  事务控制 (TCL)— 禁止 COMMIT / ROLLBACK / BEGIN
  RULE-S006  权限变更 (DCL)— 禁止 GRANT / REVOKE
  RULE-S007  白名单兜底    — 顶层语句非 SELECT / WITH(CTE) 一律拒绝

注：规则为安全红线，不对外提供配置接口（文档未规定可配置，见 docs/全局JSON-Schema规范.md §2.4.11）。
共用 parse_sql_ast() 统一解析入口，本模块禁止独立调用 sqlglot.parse()。
"""

from __future__ import annotations

import sqlglot.expressions as exp

from src.core.exceptions import SQLSecurityBlockedError
from src.core.logger import log

from .ast_parser import parse_sql_ast


# ---------------------------------------------------------------------------
# 拦截类型常量（getattr 兼容低版本 sqlglot，缺失节点类型不崩溃）
# ---------------------------------------------------------------------------

# RULE-S002：写操作
_WRITE_OP_TYPES: tuple = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
)

# RULE-S003：DDL（sqlglot 中 ALTER 对应 exp.Alter，TruncateTable 视版本而定，getattr 兜底）
_DDL_TYPES: tuple = tuple(
    t for t in [
        exp.Create,
        exp.Drop,
        getattr(exp, "Alter", None),
        getattr(exp, "TruncateTable", None),
    ]
    if t is not None
)

# RULE-S004：存储过程 / 未识别命令
_PROC_TYPES: tuple = (exp.Command,)

# RULE-S005：TCL
_TCL_TYPES: tuple = tuple(
    t for t in [
        getattr(exp, "Transaction", None),
        getattr(exp, "Commit", None),
        getattr(exp, "Rollback", None),
        getattr(exp, "Begin", None),
    ]
    if t is not None
)

# RULE-S006：DCL
_DCL_TYPES: tuple = tuple(
    t for t in [
        getattr(exp, "Grant", None),
        getattr(exp, "Revoke", None),
    ]
    if t is not None
)

# RULE-S007：白名单（With = CTE）
_ALLOWED_TYPES: tuple = (exp.Select, exp.With)


# ---------------------------------------------------------------------------
# 公开函数
# ---------------------------------------------------------------------------

def check_sql_security(sql: str) -> None:
    """对 SQL 进行安全拦截校验，通过则静默返回，违规则抛出 SQLSecurityBlockedError。

    Args:
        sql: 待校验的 SQL 字符串。

    Raises:
        ParamError (1001):              SQL 为空 / 非字符串 / 语法解析失败（由 parse_sql_ast 透传）。
        SQLSecurityBlockedError (3001): SQL 违反安全规则，已被拦截。
    """
    # 解析入口（共享层，禁止在本模块重复调用 sqlglot.parse()）
    statements = parse_sql_ast(sql)

    # RULE-S001：多语句
    if len(statements) > 1:
        log.warning(
            f"[RULE-S001] 多语句拦截 | stmt_count={len(statements)} | sql={sql!r}"
        )
        raise SQLSecurityBlockedError(
            "禁止多语句执行，每次只允许提交单条 SQL",
            detail={
                "rule": "RULE-S001",
                "stmt_count": len(statements),
                "sql": sql,
            },
        )

    stmt = statements[0]

    # RULE-S002：写操作
    if isinstance(stmt, _WRITE_OP_TYPES):
        op = type(stmt).__name__.upper()
        log.warning(f"[RULE-S002] 写操作拦截 | op={op} | sql={sql!r}")
        raise SQLSecurityBlockedError(
            f"禁止执行写操作（{op}），仅允许只读查询",
            detail={"rule": "RULE-S002", "operation": op, "sql": sql},
        )

    # RULE-S003：DDL
    if isinstance(stmt, _DDL_TYPES):
        op = type(stmt).__name__.upper()
        log.warning(f"[RULE-S003] DDL 拦截 | op={op} | sql={sql!r}")
        raise SQLSecurityBlockedError(
            f"禁止执行数据定义语句（{op}），仅允许只读查询",
            detail={"rule": "RULE-S003", "operation": op, "sql": sql},
        )

    # RULE-S004：存储过程 / 未识别命令
    if isinstance(stmt, _PROC_TYPES):
        log.warning(f"[RULE-S004] 存储过程/未识别命令拦截 | sql={sql!r}")
        raise SQLSecurityBlockedError(
            "禁止调用存储过程或执行未知命令",
            detail={"rule": "RULE-S004", "sql": sql},
        )

    # RULE-S005：TCL
    if _TCL_TYPES and isinstance(stmt, _TCL_TYPES):
        op = type(stmt).__name__.upper()
        log.warning(f"[RULE-S005] 事务控制拦截 | op={op} | sql={sql!r}")
        raise SQLSecurityBlockedError(
            f"禁止执行事务控制语句（{op}）",
            detail={"rule": "RULE-S005", "operation": op, "sql": sql},
        )

    # RULE-S006：DCL
    if _DCL_TYPES and isinstance(stmt, _DCL_TYPES):
        op = type(stmt).__name__.upper()
        log.warning(f"[RULE-S006] 权限变更拦截 | op={op} | sql={sql!r}")
        raise SQLSecurityBlockedError(
            f"禁止执行权限变更语句（{op}）",
            detail={"rule": "RULE-S006", "operation": op, "sql": sql},
        )

    # RULE-S007：白名单兜底
    if not isinstance(stmt, _ALLOWED_TYPES):
        op = type(stmt).__name__
        log.warning(f"[RULE-S007] 白名单兜底拦截 | stmt_type={op} | sql={sql!r}")
        raise SQLSecurityBlockedError(
            f"不允许的语句类型（{op}），仅允许 SELECT 查询",
            detail={"rule": "RULE-S007", "stmt_type": op, "sql": sql},
        )

    log.debug(f"SQL 安全校验通过 | sql={sql!r}")
