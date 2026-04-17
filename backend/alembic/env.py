from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import get_settings
from app.db.base import Base
from app.modules.ledger.models import LedgerTemplate, LedgerTask, LedgerInstance, DeviceBuffer
from app.modules.user.models import (
    ExternalIdentity,
    Org,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
)

# 这是 Alembic 的配置对象，用于读取当前 .ini 配置中的值
config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# 解析配置文件以配置 Python 日志
# 这一行会初始化日志器
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 在这里加入模型的 MetaData
# 以支持“自动生成”功能
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# 可从配置中获取其他 env.py 所需的值：
# my_important_option = config.get_main_option("my_important_option")
# ... 等


def run_migrations_offline() -> None:
    """以“离线”模式运行迁移。

    此模式下仅使用 URL 配置上下文，不创建 Engine。
    也可以传入 Engine，但这里会跳过创建，
    因此不需要 DBAPI 可用。

    在这里调用 context.execute() 会把 SQL 输出到脚本内容中。

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """以“在线”模式运行迁移。

    此模式需要创建 Engine，并把连接绑定到迁移上下文。

    """
    section = config.get_section(config.config_ini_section, {})
    db_url = section.get("sqlalchemy.url")
    if db_url:
        section["sqlalchemy.url"] = (
            db_url.replace("+aiosqlite", "")
            .replace("+asyncpg", "+psycopg")
            .replace("+aiomysql", "+pymysql")
        )

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
