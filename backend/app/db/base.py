# 文件路径：app/db/base.py
# 【新版本】使用 SQLAlchemy 2.0 推荐的 DeclarativeBase
# 这种写法对 IDE 提示更友好，也是 Alembic 迁移的推荐标准
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 标准基类
    替代了旧版本的 declarative_base() 工厂函数
    """
    pass
