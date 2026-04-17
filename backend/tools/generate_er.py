# 文件路径：tools/generate_er.py
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

docs_dir = os.path.join(project_root, "docs")
if not os.path.exists(docs_dir):
    os.makedirs(docs_dir)

# ==========================================
# 1. 引入所有模型 (关键修改：加入 DeviceBuffer)
# ==========================================
try:
    from app.modules.user.models import User, Role, Org, Tenant, UserRole, Permission, RolePermission
    # 【修改点】这里加上 DeviceBuffer
    from app.modules.ledger.models import LedgerTemplate, LedgerTask, LedgerInstance, DeviceBuffer
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请检查 models.py 是否已包含 DeviceBuffer 类")
    sys.exit(1)

def get_column_type(col):
    try:
        return str(col.type).split('(')[0]
    except:
        return "String"

def generate_mermaid():
    # 【修改点】列表里加上 DeviceBuffer
    models = [
        Tenant, Org, Role, User, UserRole, Permission, RolePermission,
        LedgerTemplate, LedgerTask, LedgerInstance, DeviceBuffer
    ]
    
    # 动态获取表名
    t_tenant = Tenant.__tablename__
    t_org = Org.__tablename__
    t_user = User.__tablename__
    t_role = Role.__tablename__
    t_user_role = UserRole.__tablename__
    t_perm = Permission.__tablename__
    t_role_perm = RolePermission.__tablename__
    
    t_template = LedgerTemplate.__tablename__
    t_task = LedgerTask.__tablename__
    t_instance = LedgerInstance.__tablename__
    # 【修改点】获取缓冲表表名
    t_buffer = DeviceBuffer.__tablename__

    lines = []
    lines.append("```mermaid")
    lines.append("erDiagram")
    lines.append("    %% 智慧食安平台 ER图 (Module 1 + Module 2 完整版)")
    
    for model in models:
        table_name = model.__tablename__
        lines.append(f"    {table_name} {{")
        for column in model.__table__.columns:
            col_name = column.name
            col_type = get_column_type(column)
            comment = column.comment if column.comment else ""
            key_mark = "PK" if column.primary_key else ("FK" if column.foreign_keys else "")
            lines.append(f"        {col_type} {col_name} {key_mark} \"{comment}\"")
        lines.append("    }")

    lines.append("\n    %% --- 关系定义 (动态表名) ---")
    lines.append(f"    {t_tenant} ||--|{{ {t_org} : \"owns\"")
    lines.append(f"    {t_tenant} ||--|{{ {t_user} : \"owns\"")
    lines.append(f"    {t_org} ||--|{{ {t_user} : \"belongs_to\"")
    lines.append(f"    {t_user} ||--|{{ {t_user_role} : \"has\"")
    lines.append(f"    {t_role} ||--|{{ {t_user_role} : \"has\"")
    lines.append(f"    {t_role} ||--|{{ {t_role_perm} : \"has\"")
    lines.append(f"    {t_perm} ||--|{{ {t_role_perm} : \"granted\"")

    lines.append(f"    %% 模块二关系")
    lines.append(f"    {t_template} ||--|{{ {t_task} : \"defines\"")
    lines.append(f"    {t_template} ||--|{{ {t_instance} : \"instantiates\"")
    lines.append(f"    {t_task} ||--|{{ {t_instance} : \"generates\"")
    lines.append(f"    {t_org} ||--|{{ {t_instance} : \"canteen_audit\"")
    
    # 【修改点】加上缓冲表的关系（虽然它没有物理外键，但逻辑上属于 Tenant）
    lines.append(f"    {t_tenant} ||--|{{ {t_buffer} : \"buffers\"")

    lines.append("```")
    
    output_path = os.path.join(docs_dir, "er_diagram.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✅ ER图已生成至: {output_path}")

if __name__ == "__main__":
    generate_mermaid()