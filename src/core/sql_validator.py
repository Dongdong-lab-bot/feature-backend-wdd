"""SQL 安全拦截器 - 基于 sqlglot 的全局统一 SQL 校验"""

import random
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import sqlglot
from sqlglot import exp

from src.core.logger import log


@dataclass
class ValidationResult:
    """SQL 校验结果"""

    success: bool
    blocked: bool
    reason: Optional[str] = None
    risk_level: str = "safe"  # "safe" | "warning" | "blocked"
    detail: dict = field(default_factory=dict)


@dataclass
class WhitelistRule:
    """白名单规则，支持库+表+操作粒度"""

    table: str
    db: Optional[str] = None
    allowed_operations: set[str] = field(default_factory=lambda: {"*"})


@dataclass
class SQLGuardConfig:
    """SQL 安全拦截器配置"""

    enable: bool = True
    sql_dialect: str = "mysql"
    blocked_operations: set[str] = field(
        default_factory=lambda: {
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
            "CALL", "BEGIN", "COMMIT", "ROLLBACK", "GRANT", "REVOKE", "EXEC", "SHOW"
        }
    )
    require_where_on_tables: set[str] = field(default_factory=lambda: {"*"})
    require_limit_on_tables: set[str] = field(default_factory=lambda: {"*"})
    max_rows_without_limit: int = 10000
    whitelist_rules: list = field(default_factory=list)
    custom_validators: list = field(default_factory=list)
    sql_param_names: list[str] = field(default_factory=lambda: ["sql"])
    log_sampling_rate: float = 1.0


class SQLGuard:
    """SQL 安全拦截器核心类"""

    def __init__(self, config: Optional[SQLGuardConfig] = None):
        self.config = config or SQLGuardConfig()

    def validate(self, sql: str) -> ValidationResult:
        """解析 SQL 并执行安全+性能校验，返回结果（不抛异常）"""
        if not self.config.enable:
            return ValidationResult(success=True, blocked=False)

        # 采样控制（仅对通过校验的 SQL 生效；被拦截的操作强制审计）
        skip_audit = random.random() > self.config.log_sampling_rate

        # 先进行字符串级别快速检查（处理 sqlglot 无法解析的语句）
        string_level_issues = self._check_string_level_operations(sql)
        if string_level_issues:
            result = ValidationResult(
                success=False,
                blocked=True,
                risk_level="blocked",
                reason=f"Blocked dangerous operation: {', '.join(string_level_issues)}",
                detail={"operations": string_level_issues},
            )
            # 被拦截的危险操作强制审计，不受采样率影响
            self._log_audit(sql, result)
            return result

        try:
            ast = sqlglot.parse_one(sql, dialect=self.config.sql_dialect)
        except Exception:
            # 解析失败时无法确认 SQL 安全性，必须阻断
            result = ValidationResult(
                success=False,
                blocked=True,
                risk_level="blocked",
                reason="SQL parse error: unable to verify safety",
            )
            # 解析失败属于危险操作，强制审计不受采样率影响
            self._log_audit(sql, result)
            return result

        # 执行安全校验
        security_issues = self._check_write_operations(ast)
        if security_issues:
            result = ValidationResult(
                success=False,
                blocked=True,
                risk_level="blocked",
                reason=f"Blocked write operation: {', '.join(security_issues)}",
                detail={"operations": security_issues},
            )
            # 被拦截的写入操作强制审计，不受采样率影响
            self._log_audit(sql, result)
            return result

        # 执行性能校验
        perf_issues = self._check_performance(ast)
        if perf_issues:
            result = ValidationResult(
                success=False,
                blocked=True,
                risk_level="blocked",
                reason=f"Performance risk: {', '.join(perf_issues)}",
                detail={"issues": perf_issues},
            )
            # 被拦截的性能风险操作强制审计，不受采样率影响
            self._log_audit(sql, result)
            return result

        # 执行自定义校验钩子
        custom_result = self._run_custom_validators(ast)
        if custom_result:
            if custom_result.blocked:
                # 被拦截的自定义校验结果同样强制审计
                self._log_audit(sql, custom_result)
            elif not skip_audit:
                self._log_audit(sql, custom_result)
            return custom_result

        result = ValidationResult(success=True, blocked=False)
        if not skip_audit:
            self._log_audit(sql, result)
        return result

    def _log_audit(self, sql: str, result: ValidationResult) -> None:
        """记录审计日志"""
        desensitized_sql = self._desensitize_sql(sql)
        log.audit(
            "SQL_GUARD_VALIDATION",
            sql=desensitized_sql[:500],
            success=result.success,
            blocked=result.blocked,
            risk_level=result.risk_level,
            reason=result.reason,
        )

    def _desensitize_sql(self, sql: str) -> str:
        """SQL 脱敏：替换字符串字面值、数字字面值、敏感数据格式"""
        # 替换字符串字面值（单引号和双引号）
        sql = re.sub(r"'[^']*'", "'?'", sql)
        sql = re.sub(r'"[^"]*"', '"?"', sql)

        # 替换敏感数据格式：手机号、身份证、邮箱
        sql = re.sub(r"1[3-9]\d{9}", "?", sql)  # 手机号
        sql = re.sub(r"\d{17}[\dXx]|\d{15}", "?", sql)  # 身份证
        sql = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "?", sql)  # 邮箱

        return sql

    @staticmethod
    def _strip_sql_comments(sql: str) -> str:
        """移除 SQL 注释：/*...*/、--...、#..."""
        # 多行注释 /* ... */
        sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
        # 单行注释 -- ...
        sql = re.sub(r"--[^\n]*", " ", sql)
        # MySQL 风格 # ...
        sql = re.sub(r"#[^\n]*", " ", sql)
        return sql

    def _check_string_level_operations(self, sql: str) -> list[str]:
        """字符串级别快速检查，处理 sqlglot 无法解析的语句"""
        issues = []
        sql_clean = self._strip_sql_comments(sql).strip().upper()

        # 检查 CALL 语句（存储过程调用）
        if sql_clean.startswith("CALL "):
            issues.append("CALL")

        # 检查事务控制语句
        if sql_clean.startswith("BEGIN TRANSACTION") or sql_clean == "BEGIN":
            issues.append("BEGIN")
        if sql_clean == "COMMIT":
            issues.append("COMMIT")
        if sql_clean == "ROLLBACK":
            issues.append("ROLLBACK")

        # 检查 EXEC 语句（SQL Server 存储过程执行）
        if sql_clean.startswith("EXEC "):
            issues.append("EXEC")

        return issues

    def _check_write_operations(self, ast: exp.Expression) -> list[str]:
        """检查破坏性写操作，返回拦截的操作列表"""
        blocked = []
        for node in ast.walk():
            op_type = type(node).__name__.upper()
            # Map AST class names to operation names
            op_map = {
                "TRUNCATETABLE": "TRUNCATE",
                "GRANT": "GRANT",
                "REVOKE": "REVOKE",
                "SHOW": "SHOW",
                "EXEC": "EXEC",
                "CALL": "CALL",
            }
            op_type = op_map.get(op_type, op_type)
            if op_type in self.config.blocked_operations:
                # 检查白名单规则
                if not self._is_whitelisted(node, op_type):
                    blocked.append(op_type)
        return list(dict.fromkeys(blocked))  # 去重保持顺序

    def _is_whitelisted(self, node: exp.Expression, operation: str) -> bool:
        """检查节点是否匹配白名单规则"""
        table_name = self._get_table_name(node)
        for rule in self.config.whitelist_rules:
            if self._match_rule(rule, table_name, operation):
                return True
        return False

    def _get_table_name(self, node: exp.Expression) -> Optional[str]:
        """从 AST 节点提取表名"""
        if isinstance(node, exp.Insert):
            if node.this and isinstance(node.this, exp.Table):
                return node.this.name
            if node.expression and hasattr(node.expression, "name"):
                return node.expression.name
        if isinstance(node, exp.Update):
            if node.this and isinstance(node.this, exp.Table):
                return node.this.name
        if isinstance(node, exp.Delete):
            if node.this and isinstance(node.this, exp.Table):
                return node.this.name
        if isinstance(node, exp.Drop):
            if node.this and isinstance(node.this, exp.Table):
                return node.this.name
        if isinstance(node, exp.Alter):
            if node.this and isinstance(node.this, exp.Table):
                return node.this.name
        if isinstance(node, exp.Create):
            if node.this and isinstance(node.this, exp.Table):
                return node.this.name
        if isinstance(node, exp.TruncateTable):
            if node.expressions:
                first = node.expressions[0]
                if isinstance(first, exp.Table):
                    return first.name
            if node.this and isinstance(node.this, exp.Table):
                return node.this.name
        return None

    def _match_rule(self, rule: WhitelistRule, table_name: Optional[str], operation: str) -> bool:
        """匹配白名单规则，支持通配符"""
        if table_name is None:
            return False
        import fnmatch
        if not fnmatch.fnmatch(table_name, rule.table):
            return False
        if "*" in rule.allowed_operations:
            return True
        if operation in rule.allowed_operations:
            return True
        return False

    def _check_performance(self, ast: exp.Expression) -> list[str]:
        """检查性能风险，返回问题列表"""
        issues = []
        issues.extend(self._check_where_clause(ast))
        issues.extend(self._check_join_on(ast))
        issues.extend(self._check_limit_clause(ast))
        return issues

    def _check_where_clause(self, ast: exp.Expression) -> list[str]:
        """检查 SELECT/UPDATE/DELETE 是否有 WHERE 子句，递归检查子查询和 CTE"""
        issues = []
        checked_nodes = set()

        for node in ast.walk():
            if isinstance(node, (exp.Select, exp.Update, exp.Delete)):
                node_id = id(node)
                if node_id in checked_nodes:
                    continue
                checked_nodes.add(node_id)

                # 递归检查该节点及其所有子节点是否有 WHERE
                has_where = self._has_any_where(node)

                if not has_where:
                    # 检查是否有 LIMIT 且 LIMIT <= 阈值
                    limit_value = self._get_limit_value(node)
                    if limit_value is not None and limit_value <= self.config.max_rows_without_limit:
                        continue
                    table_name = self._extract_main_table(node)
                    if self._table_requires_where(table_name):
                        issues.append(f"Missing WHERE clause on table '{table_name or 'unknown'}'")
        return issues

    def _has_any_where(self, node: exp.Expression) -> bool:
        """递归检查节点及其所有子查询中是否有 WHERE 子句"""
        # 直接检查当前节点
        if hasattr(node, "args") and node.args.get("where"):
            return True
        if isinstance(node, exp.Where):
            return True

        # 递归检查所有子节点
        for child in node.walk():
            if isinstance(child, exp.Where):
                return True
        return False

    def _extract_main_table(self, node: exp.Expression) -> Optional[str]:
        """从查询节点提取主表名"""
        if isinstance(node, exp.Select):
            from_clause = node.args.get("from") or node.args.get("from_")
            if from_clause and isinstance(from_clause, exp.From):
                if isinstance(from_clause.this, exp.Table):
                    return from_clause.this.name
        elif isinstance(node, (exp.Update, exp.Delete)):
            if node.this and isinstance(node.this, exp.Table):
                return node.this.name
        return None

    def _table_requires_where(self, table_name: Optional[str]) -> bool:
        """检查表是否需要 WHERE 子句"""
        if "*" in self.config.require_where_on_tables:
            return True
        if table_name and table_name in self.config.require_where_on_tables:
            return True
        return False

    def _get_limit_value(self, node: exp.Expression) -> Optional[int]:
        """从查询节点提取 LIMIT 值，兼容多方言"""
        if not hasattr(node, "args"):
            return None
        limit_node = node.args.get("limit")
        if limit_node is None:
            return None

        # MySQL / PostgreSQL / SQLite LIMIT (also covers TSQL TOP normalized to Limit)
        if isinstance(limit_node, exp.Limit):
            expr = getattr(limit_node, "expression", None)
            if isinstance(expr, exp.Literal):
                try:
                    return int(expr.this)
                except (ValueError, TypeError):
                    return None
            return None

        # PostgreSQL FETCH FIRST
        if isinstance(limit_node, exp.Fetch):
            count = getattr(limit_node, "args", {}).get("count")
            if isinstance(count, exp.Literal):
                try:
                    return int(count.this)
                except (ValueError, TypeError):
                    return None
            return None

        return None

    def _check_join_on(self, ast: exp.Expression) -> list[str]:
        """检查 JOIN 是否有 ON 条件，拦截显式 CROSS JOIN"""
        issues = []
        for node in ast.walk():
            if isinstance(node, exp.Join):
                # 检查是否是 CROSS JOIN
                if hasattr(node, "kind") and node.kind and node.kind.upper() == "CROSS":
                    issues.append("CROSS JOIN detected (explicit cartesian product)")
                    continue

                # 检查是否有 ON 条件
                # node.on is a bound method in sqlglot, use args["on"] instead
                has_on = bool(node.args.get("on"))

                if not has_on:
                    issues.append("JOIN without ON condition (cartesian product risk)")
        return issues

    def _check_limit_clause(self, ast: exp.Expression) -> list[str]:
        """检查查询是否有 LIMIT / TOP / FETCH FIRST"""
        issues = []
        for node in ast.walk():
            if isinstance(node, exp.Select):
                limit_value = self._get_limit_value(node)
                if limit_value is None:
                    table_name = self._extract_main_table(node)
                    if self._table_requires_limit(table_name):
                        issues.append(f"Missing LIMIT clause on table '{table_name or 'unknown'}'")
        return issues

    def _table_requires_limit(self, table_name: Optional[str]) -> bool:
        """检查表是否需要 LIMIT 子句"""
        if "*" in self.config.require_limit_on_tables:
            return True
        if table_name and table_name in self.config.require_limit_on_tables:
            return True
        return False

    def validate_or_raise(self, sql: str) -> ValidationResult:
        """校验 SQL，若 blocked 则抛出对应 ProjectBaseException"""
        result = self.validate(sql)
        if result.blocked:
            if result.detail and "operations" in result.detail:
                from src.core.exceptions import SQLSecurityBlockedError
                raise SQLSecurityBlockedError(
                    message=result.reason,
                    detail=result.detail,
                )
            else:
                from src.core.exceptions import SQLPerformanceBlockedError
                raise SQLPerformanceBlockedError(
                    message=result.reason,
                    detail=result.detail,
                )
        return result

    def _run_custom_validators(self, ast: exp.Expression) -> Optional[ValidationResult]:
        """执行自定义校验钩子"""
        for validator in self.config.custom_validators:
            try:
                valid, reason = validator(ast)
                if not valid:
                    return ValidationResult(
                        success=False,
                        blocked=True,
                        risk_level="blocked",
                        reason=reason or "Custom validation failed",
                    )
            except Exception as exc:
                # 自定义校验器异常不应阻断主流程，但必须记录日志
                log.error(f"SQL 自定义校验器异常: {exc}")
                continue
        return None

    def protect(self, func=None, sql_param_names=None):
        """装饰器：自动拦截被装饰函数参数中的 SQL 字符串
        支持 @guard.protect 和 @guard.protect() 两种写法
        """
        param_names = sql_param_names or self.config.sql_param_names

        def decorator(f):
            import functools

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # 检查位置参数
                for arg in args:
                    if isinstance(arg, str) and any(
                        arg.strip().upper().startswith(prefix)
                        for prefix in ("SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "WITH")
                    ):
                        self.validate_or_raise(arg)

                # 检查关键字参数（按参数名匹配）
                for name, value in kwargs.items():
                    if name in param_names and isinstance(value, str):
                        self.validate_or_raise(value)

                return f(*args, **kwargs)
            return wrapper

        if func is not None:
            return decorator(func)
        return decorator
