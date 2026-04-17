# 文件路径：tools/export_ddl.py
import sys
import os
from sqlalchemy import create_mock_engine

# 1. 路径修复
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from app.db.base import Base

# ==========================================
# 核心修改点：引入所有模块的模型
# ==========================================
# 1. 模块一：用户与组织
from app.modules.user import models as user_models
# 2. 模块二：台账 (新增！)
from app.modules.ledger import models as ledger_models

def dump(sql, *multiparams, **params):
    """打印生成的SQL"""
    # 强制转换字符串，防止类型错误
    print(str(sql.compile(dialect=engine.dialect)).strip() + ";")

def generate_sql():
    global engine
    # 模拟 MySQL
    engine = create_mock_engine("mysql+pymysql://", dump)
    
    print("-- 智慧食安平台 数据库初始化脚本 (含模块一 & 模块二)")
    print("-- 生成时间：实时生成")
    print("-- ----------------------------")
    Base.metadata.create_all(engine, checkfirst=False)

if __name__ == "__main__":
    generate_sql()