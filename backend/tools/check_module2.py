# 文件路径：tools/check_module2.py
import sys
import os
import inspect

# 1. 修正路径，确保能导入 app
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

try:
    from app.modules.ledger.models import LedgerInstance, LedgerTemplate, LedgerTask
    from app.db.mixins import TenantMixin
    from sqlalchemy.orm import Mapped
    print("✅ 模块导入成功")
except ImportError as e:
    print(f"❌ 导入失败，请检查 models.py 是否创建: {e}")
    sys.exit(1)

def check_red_lines():
    print("\n--- 开始检查模块二红线指标 ---")
    model = LedgerInstance
    
    # 1. 检查 TenantMixin (租户隔离)
    if issubclass(model, TenantMixin):
        print("✅ [红线1] LedgerInstance 已继承 TenantMixin (租户隔离)")
    else:
        print("❌ [红线1] LedgerInstance 未继承 TenantMixin！验收必挂！")

    # 2. 检查关键字段是否存在
    props = dir(model)
    required_fields = [
        ("schema_snapshot", "快照"),
        ("content", "填报内容"),
        ("security_hash", "防篡改Hash")
    ]
    
    for field, name in required_fields:
        if field in props:
            print(f"✅ [红线2] 字段 '{field}' ({name}) 存在")
        else:
            print(f"❌ [红线2] 缺失关键字段 '{field}'！验收必挂！")

    # 3. 检查 SQLAlchemy 2.0 语法
    # 简单检查 annotations 是否使用了 Mapped
    annotations = model.__annotations__
    if 'schema_snapshot' in annotations and 'Mapped' in str(annotations['schema_snapshot']):
         print("✅ [红线3] 使用了 SQLAlchemy 2.0 Mapped 语法")
    else:
         print("❌ [红线3] 未检测到 Mapped 语法，可能还在用旧版 Column！")

    print("\n--- 检查结束 ---")

if __name__ == "__main__":
    check_red_lines()