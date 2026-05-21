"""
性能灾难防御模块（AST 通用逻辑）

本模块负责资源边界审查，基于 SQL 语法树实现以下防护：
1. 拦截无 WHERE 条件的全表扫描（针对 SELECT 语句）
2. 拦截无 ON 条件的笛卡尔积（针对多表 JOIN）
3. 智能识别并强制追加 LIMIT 限制

核心设计原则：
- 与安全校验模块共用 parse_sql_ast 统一解析入口
- 纯 AST 解析，不依赖底层 Schema，确保通用性
- 支持自动修复（如追加 LIMIT）而非单纯拦截
- 输出结构化校验结果，便于后续审计和监控

使用规范：
- 本模块仅做性能校验，不负责业务逻辑校验
- 校验通过后返回处理后的 SQL，可能已被自动修复
- 校验失败时抛出 SQLPerformanceBlockedError 异常
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any

import sqlglot
from sqlglot import exp
from sqlglot.expressions import Expression, Select, Join, Limit
from pydantic import BaseModel, Field

from .ast_parser import parse_sql_ast
from src.core.exceptions import SQLPerformanceBlockedError
from src.core.logger import log


class ASTPerformanceCheckResult(BaseModel):
    """性能校验结果 Pydantic 模型"""
    processed_sql: str
    is_modified: bool
    reason: str = ""
    auto_limit_value: Optional[int] = None
    trace_id: str = ""
    issues: List[Dict[str, Any]] = Field(default_factory=list)


class PerformanceConfig:
    """性能校验配置类"""
    # 默认 LIMIT 值（当检测到风险且无 LIMIT 时自动追加）
    DEFAULT_LIMIT: int = 1000
    # 最大允许的 LIMIT 值（超过此值视为风险）
    MAX_ALLOWED_LIMIT: int = 100000
    # 是否启用自动修复（追加 LIMIT）
    AUTO_FIX_ENABLED: bool = True
    # 是否拦截笛卡尔积
    BLOCK_CARTESIAN_JOIN: bool = True
    # 是否拦截全表扫描
    BLOCK_FULL_TABLE_SCAN: bool = True


def _has_where_clause(select_stmt: Select) -> bool:
    """检测 SELECT 语句是否包含 WHERE 子句"""
    return select_stmt.args.get('where') is not None


def _has_limit_clause(select_stmt: Select) -> bool:
    """检测 SELECT 语句是否包含 LIMIT 子句"""
    return select_stmt.find(exp.Limit) is not None


def _get_limit_value(select_stmt: Select) -> Optional[int]:
    """获取 LIMIT 子句的值"""
    limit_node = select_stmt.find(exp.Limit)
    if limit_node:
        limit_expr = limit_node.expression
        if isinstance(limit_expr, exp.Literal):
            val = limit_expr.this
            if isinstance(val, int):
                return val
            elif isinstance(val, str) and val.isdigit():
                return int(val)
            elif isinstance(val, str):
                try:
                    return int(float(val))
                except (ValueError, TypeError):
                    pass
    return None


def _has_join_clause(select_stmt: Select) -> bool:
    """检测 SELECT 语句是否包含 JOIN 子句"""
    return select_stmt.find(exp.Join) is not None


def _has_on_condition(join_node: Join) -> bool:
    """检测 JOIN 节点是否包含 ON 条件"""
    # ON 条件通常在 join_node.args.get('on') 中
    return join_node.args.get('on') is not None


def _count_tables(select_stmt: Select) -> int:
    """统计 SELECT 语句中涉及的表数量"""
    tables = []
    
    def collect_tables(node: Expression):
        if isinstance(node, exp.Table):
            table_name = node.args.get('this')
            if table_name and table_name not in tables:
                tables.append(table_name)
        for child in node.iter_expressions():
            collect_tables(child)
    
    collect_tables(select_stmt)
    return len(tables)


def _check_cartesian_join(select_stmt: Select) -> List[Dict[str, Any]]:
    """检测笛卡尔积风险
    
    笛卡尔积风险场景：
    1. 多表 JOIN 但缺少 ON 条件
    2. CROSS JOIN（显式笛卡尔积）
    
    Returns:
        风险列表，每项包含风险类型和位置信息
    """
    issues = []
    join_nodes = list(select_stmt.find_all(exp.Join))
    
    for idx, join_node in enumerate(join_nodes):
        # 检测 CROSS JOIN
        join_type = join_node.args.get('join_type')
        if join_type and join_type.upper() == 'CROSS':
            issues.append({
                'type': 'cartesian_join',
                'subtype': 'explicit_cross_join',
                'message': f"检测到显式 CROSS JOIN，可能产生笛卡尔积",
                'position': f'join_{idx}',
            })
            continue
        
        # 检测缺少 ON 条件的 JOIN
        if not _has_on_condition(join_node):
            issues.append({
                'type': 'cartesian_join',
                'subtype': 'missing_on_condition',
                'message': f"JOIN 缺少 ON 条件，可能产生笛卡尔积",
                'position': f'join_{idx}',
            })
    
    return issues


def _check_full_table_scan(select_stmt: Select) -> Optional[Dict[str, Any]]:
    """检测全表扫描风险
    
    全表扫描风险场景：
    1. 单表查询且无 WHERE 条件
    2. 无 LIMIT 限制（增加风险等级）
    
    Returns:
        风险信息（如果检测到），否则返回 None
    """
    # 如果有 JOIN，通常不是简单的全表扫描
    if _has_join_clause(select_stmt):
        return None
    
    # 检查表数量（单表查询更可能是全表扫描）
    table_count = _count_tables(select_stmt)
    if table_count != 1:
        return None
    
    # 检测是否有 WHERE 条件
    if not _has_where_clause(select_stmt):
        has_limit = _has_limit_clause(select_stmt)
        return {
            'type': 'full_table_scan',
            'message': f"检测到无 WHERE 条件的单表查询，可能导致全表扫描",
            'has_limit': has_limit,
            'risk_level': 'high' if not has_limit else 'medium',
        }
    
    return None


def _check_limit_exceeded(select_stmt: Select) -> Optional[Dict[str, Any]]:
    """检测 LIMIT 值是否超过安全阈值"""
    limit_value = _get_limit_value(select_stmt)
    if limit_value is not None and limit_value > PerformanceConfig.MAX_ALLOWED_LIMIT:
        return {
            'type': 'limit_exceeded',
            'message': f"LIMIT 值 {limit_value} 超过安全阈值 {PerformanceConfig.MAX_ALLOWED_LIMIT}",
            'current_limit': limit_value,
            'max_allowed': PerformanceConfig.MAX_ALLOWED_LIMIT,
        }
    return None


def _add_limit_clause(select_stmt: Select, limit_value: int) -> Select:
    """为 SELECT 语句添加 LIMIT 子句"""
    # 创建 LIMIT 表达式
    limit_expr = exp.Limit(this=exp.Literal(this=limit_value, is_string=False))
    # 添加到 SELECT 语句
    select_stmt.set('expressions', [*select_stmt.expressions, limit_expr])
    return select_stmt


def validate_ast_performance(
    sql: str,
    dialect: str = "mysql",
    trace_id: str = "",
    config: Optional[PerformanceConfig] = None
) -> ASTPerformanceCheckResult:
    """
    SQL 性能校验主入口
    
    基于 AST 语法树进行性能风险检测：
    1. 检测无 WHERE 条件的全表扫描
    2. 检测无 ON 条件的笛卡尔积
    3. 检测过大的 LIMIT 值
    4. 自动追加 LIMIT 限制（如果启用）
    
    Args:
        sql: 待校验的 SQL 字符串
        dialect: SQL 方言，默认 "mysql"
        trace_id: 追踪 ID，用于日志关联
        config: 性能校验配置（可选）
    
    Returns:
        ASTPerformanceCheckResult: 校验结果，包含处理后的 SQL 和问题列表
    
    Raises:
        SQLPerformanceBlockedError: 当检测到严重性能风险且无法自动修复时
    """
    # 使用默认配置
    if config is None:
        config = PerformanceConfig()
    
    # 解析 SQL 为 AST
    statements = parse_sql_ast(sql, dialect=dialect)
    
    # 仅处理第一条语句（多语句已被安全校验拦截）
    stmt = statements[0]
    
    # 仅处理 SELECT 语句
    if not isinstance(stmt, Select):
        return ASTPerformanceCheckResult(
            processed_sql=sql,
            is_modified=False,
            reason="非 SELECT 语句，跳过性能校验",
            trace_id=trace_id,
        )
    
    issues: List[Dict[str, Any]] = []
    is_modified = False
    auto_limit_value = None
    
    # ── 检测1：笛卡尔积风险 ──────────────────────────────────────────────────
    cartesian_issues = _check_cartesian_join(stmt)
    if cartesian_issues:
        issues.extend(cartesian_issues)
        if config.BLOCK_CARTESIAN_JOIN:
            log.warning(
                f"性能校验拦截：检测到笛卡尔积风险 | trace_id={trace_id} | issues={cartesian_issues}"
            )
            raise SQLPerformanceBlockedError(
                message="检测到笛卡尔积风险，已拦截",
                detail={
                    "sql": sql,
                    "issues": cartesian_issues,
                    "trace_id": trace_id,
                }
            )
    
    # ── 检测2：全表扫描风险 ──────────────────────────────────────────────────
    scan_issue = _check_full_table_scan(stmt)
    if scan_issue:
        issues.append(scan_issue)
        if config.BLOCK_FULL_TABLE_SCAN and not scan_issue.get('has_limit'):
            # 如果没有 LIMIT 且启用了拦截，抛出异常
            log.warning(
                f"性能校验拦截：检测到全表扫描风险 | trace_id={trace_id} | issue={scan_issue}"
            )
            raise SQLPerformanceBlockedError(
                message="检测到全表扫描风险（无 WHERE 条件且无 LIMIT 限制），已拦截",
                detail={
                    "sql": sql,
                    "issue": scan_issue,
                    "trace_id": trace_id,
                }
            )
    
    # ── 检测3：LIMIT 超限风险 ────────────────────────────────────────────────
    limit_issue = _check_limit_exceeded(stmt)
    if limit_issue:
        issues.append(limit_issue)
        # LIMIT 超限直接拦截
        log.warning(
            f"性能校验拦截：LIMIT 值超限 | trace_id={trace_id} | issue={limit_issue}"
        )
        raise SQLPerformanceBlockedError(
            message=f"LIMIT 值超过安全阈值 {config.MAX_ALLOWED_LIMIT}",
            detail={
                "sql": sql,
                "issue": limit_issue,
                "trace_id": trace_id,
            }
        )
    
    # ── 自动修复：追加 LIMIT ──────────────────────────────────────────────────
    if config.AUTO_FIX_ENABLED and not _has_limit_clause(stmt):
        # 对于有风险的查询，自动追加 LIMIT
        if issues or _count_tables(stmt) > 1:
            stmt = _add_limit_clause(stmt, config.DEFAULT_LIMIT)
            is_modified = True
            auto_limit_value = config.DEFAULT_LIMIT
    
    # 将 AST 转换回 SQL 字符串
    processed_sql = stmt.sql(dialect=dialect)
    
    # 记录审计日志
    if issues or is_modified:
        log.audit(
            f"SQL 性能校验完成 | modified={is_modified} | issues={len(issues)} | trace_id={trace_id}"
        )
    
    return ASTPerformanceCheckResult(
        processed_sql=processed_sql,
        is_modified=is_modified,
        reason="性能校验通过" if not issues else "; ".join(issue['message'] for issue in issues),
        auto_limit_value=auto_limit_value,
        trace_id=trace_id,
        issues=issues,
    )
