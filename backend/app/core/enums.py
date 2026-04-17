# 文件路径：app/core/enums.py
# 作用：定义系统里的“死规矩”，对应《后端API.pdf》第5章

from enum import Enum

# 对应文档 5.1 RoleType (角色类型)
class RoleType(str, Enum):
    REGULATOR = "REGULATOR"  # 监管方（政府、教育局）
    EXECUTOR = "EXECUTOR"    # 执行方（食堂、餐饮公司）

# 对应文档 5.2 OrgType (组织类型)
class OrgType(str, Enum):
    REGION = "REGION"    # 片区/行政区
    SCHOOL = "SCHOOL"    # 学校
    CANTEEN = "CANTEEN"  # 食堂
    DEPARTMENT = "DEPARTMENT" # 部门（后勤部等）

# 用户状态
class UserStatus(int, Enum):
    DISABLE = 0  # 禁用
    ENABLE = 1   # 启用


class InspectionTaskStatus(str, Enum):
    """
    巡检任务状态枚举

    状态流转图：

        PENDING -----> SUBMITTED -----> COMPLETED
           |              |
           |              v
           |           REJECTED
           |              |
           v              v
        RECTIFIED -----> COMPLETED
           |
           v
        REJECTED
    """
    PENDING = "PENDING"       # 待上报/待签字
    SUBMITTED = "SUBMITTED"   # 已上报，待审核
    REJECTED = "REJECTED"     # 审核驳回，待整改
    RECTIFIED = "RECTIFIED"   # 已整改，待复审
    COMPLETED = "COMPLETED"   # 已完成
    CANCELLED = "CANCELLED"   # 已取消