import re
import logging
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.sql.elements import TextClause

# =============================================================================
# 🛡️ 李文钊 (Security Guard) - 核心职责实现
# 防止拦截器被绕过（安全兜底）
# =============================================================================

class SecurityException(Exception):
    pass

# 定义白名单：允许不带 tenant_id 的原生 SQL
RAW_SQL_ALLOW_LIST = [
    "alembic_version",
    "select 1",
    "pg_",
    "information_schema",
    "sqlite_",
    "show tables",
    "describe ",
    "explain ",
    "pragma", # SQLite 特有
    "count(*)", # 简单的统计可能不需要 tenant_id (视情况而定，但通常业务表查询都需要)
    "menus",   # 菜单表为全局表，不含 tenant_id
    "tenants",  # 租户表为全局表，不含 tenant_id
    "permissions",  # 权限表为全局表，不含 tenant_id
    "external_identities",  # 外部身份映射表不含 tenant_id
]

def register_security_guards(session_factory, engine):
    """
    注册安全拦截器。
    该函数应在 app/db/session.py 或 main.py 启动时调用。
    
    注意：ORM 层面的多租户隔离（Write Guard）已由 app.db.tenant_interceptor.TenantSession 接管。
    此处仅保留 Engine 层面的原生 SQL 防御，作为最后一道防线。
    """
    
    # -------------------------------------------------------------------------
    # 原生 SQL 防御 (Raw SQL Guard) - 监听 Connection.before_cursor_execute
    # -------------------------------------------------------------------------
    @event.listens_for(engine, "before_cursor_execute")
    def _before_cursor_execute(conn: Connection, cursor, statement, parameters, context, executemany):
        compiled = getattr(context, "compiled", None)
        if compiled is not None and not isinstance(compiled.statement, TextClause):
            return

        stmt_str = str(statement).lower().strip()
        
        # 白名单检查
        for allow_pattern in RAW_SQL_ALLOW_LIST:
            if allow_pattern in stmt_str:
                return

        # 简单特征检测：如果包含 DML 但没有 tenant_id
        dangerous_keywords = ["insert ", "update ", "delete ", "select "]
        is_dangerous = any(k in stmt_str for k in dangerous_keywords)
        
        if is_dangerous and "tenant_id" not in stmt_str:
             msg = f"SECURITY BLOCK: Raw SQL execution blocked! Missing 'tenant_id' filter. SQL: {stmt_str[:50]}..."
             logging.error(msg)
             raise SecurityException(msg)