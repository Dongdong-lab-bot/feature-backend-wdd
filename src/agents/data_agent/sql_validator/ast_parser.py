"""
SQL 语法树统一解析入口（共享层）

本模块为 data_agent 内所有 AST 校验模块提供唯一解析入口。

使用规范（强约束）：
- security_check.py 和 performance_check.py 必须共用本模块的
  parse_sql_ast()，禁止各自独立实现 AST 解析逻辑。
- dialect 当前固定为 "mysql"
- 本函数不负责业务拦截，仅负责将 SQL 字符串转换为语法树，拦截逻辑由各校验模块自行实现。
"""

from __future__ import annotations

from typing import List

import sqlglot
from sqlglot.expressions import Expression
from sqlglot.errors import ParseError

from src.core.exceptions import ParamError
from src.core.logger import log


def parse_sql_ast(sql: str, dialect: str = "mysql") -> List[Expression]:
    """将 SQL 字符串解析为 sqlglot 语法树列表。

    统一解析入口，全组共用，禁止在 security_check / performance_check 中重复调用
    sqlglot.parse()。

    Args:
        sql:     待解析的 SQL 字符串，不得为空或纯空白。
        dialect: SQL 方言，默认 "mysql"

    Returns:
        List[Expression]：解析后的语法树节点列表，至少含 1 个元素。

    Raises:
        ParamError (错误码 1001);
            - sql 为空、非字符串，或纯空白字符串；
            - sqlglot 无法解析（语法错误）；
            - 解析结果为空列表（异常兜底）。
    """
    # ── 入参基础校验 ──────────────────────────────────────────────────────────
    if not isinstance(sql, str):
        raise ParamError(
            "SQL 必须为字符串类型",
            detail={"sql": repr(sql), "reason": "invalid_type"},
        )

    sql_stripped = sql.strip()
    if not sql_stripped:
        raise ParamError(
            "SQL 不能为空或纯空白字符串",
            detail={"sql": repr(sql), "reason": "blank_or_empty"},
        )

    # ── sqlglot 解析 ──────────────────────────────────────────────────────────
    try:
        statements: List[Expression] = sqlglot.parse(sql_stripped, dialect=dialect)
    except ParseError as exc:
        log.warning(
            f"SQL 语法解析失败 | dialect={dialect} | error={exc} | sql={sql_stripped!r}"
        )
        raise ParamError(
            "SQL 语法解析失败，无法构建语法树",
            detail={
                "sql": sql_stripped,
                "dialect": dialect,
                "parse_error": str(exc),
            },
        ) from exc

    # ── 解析结果兜底 ──────────────────────────────────────────────────────────
    # sqlglot 极少情况下会返回空列表（如输入为纯注释），此处做最后防线
    if not statements:
        raise ParamError(
            "SQL 解析结果为空，请检查输入内容",
            detail={"sql": sql_stripped, "dialect": dialect, "reason": "empty_parse_result"},
        )

    # 过滤 None（sqlglot 对空语句可能产生 None 占位符）
    valid_statements = [s for s in statements if s is not None]
    if not valid_statements:
        raise ParamError(
            "SQL 解析后无有效语句",
            detail={"sql": sql_stripped, "dialect": dialect, "reason": "all_statements_none"},
        )

    return valid_statements
