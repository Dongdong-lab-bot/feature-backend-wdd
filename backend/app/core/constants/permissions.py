# 用户与组织管理模块
USER_ADD = "user:add"
USER_EDIT = "user:edit"
USER_DELETE = "user:delete"
USER_VIEW = "user:view"
USER_ASSIGN_CANTEEN = "user:assign_canteen"
USER_ASSIGN_ROLE = "user:assign_role"

# 角色管理
ROLE_ADD = "role:add"
ROLE_EDIT = "role:edit"
ROLE_DELETE = "role:delete"
ROLE_VIEW = "role:view"
ROLE_ASSIGN_PERMISSION = "role:assign_permission"

# 食堂管理
CANTEEN_ADD = "canteen:add"
CANTEEN_EDIT = "canteen:edit"
CANTEEN_DELETE = "canteen:delete"
CANTEEN_VIEW = "canteen:view"
CANTEEN_ASSIGN_DEVICE = "canteen:assign_device"
CANTEEN_ASSIGN_CAMERA = "canteen:assign_camera"

# 部门管理
DEPARTMENT_ADD = "department:add"
DEPARTMENT_EDIT = "department:edit"
DEPARTMENT_DELETE = "department:delete"
DEPARTMENT_VIEW = "department:view"

# 数字化台账模块
LEDGER_TEMPLATE_ADD = "ledger_template:add"
LEDGER_TEMPLATE_EDIT = "ledger_template:edit"
LEDGER_TEMPLATE_DELETE = "ledger_template:delete"
LEDGER_TEMPLATE_VIEW = "ledger_template:view"
LEDGER_TEMPLATE_PUBLISH = "ledger_template:publish"
LEDGER_ADD = "ledger:add"
LEDGER_EDIT = "ledger:edit"
LEDGER_SUBMIT = "ledger:submit"
LEDGER_VIEW = "ledger:view"
LEDGER_EXPORT = "ledger:export"
LEDGER_SIGN = "ledger:sign"
LEDGER_UPLOAD_FILE = "ledger:upload_file"

# SOP管理
SOP_ADD = "sop:add"
SOP_EDIT = "sop:edit"
SOP_DELETE = "sop:delete"
SOP_VIEW = "sop:view"
SOP_VIEW_PROGRESS = "sop:view_progress"

# 巡检业务模块
# 日管控
DAILY_CREATE_TEMPLATE = "daily:create_template"
DAILY_PUBLISH = "daily:publish"
DAILY_SUBMIT = "daily:submit"
DAILY_VIEW = "daily:view"
DAILY_VIEW_PROGRESS = "daily:view_progress"
DAILY_APPROVE = "daily:approve"

# 周排查
WEEKLY_CREATE_TEMPLATE = "weekly:create_template"
WEEKLY_PUBLISH = "weekly:publish"
WEEKLY_SUBMIT = "weekly:submit"
WEEKLY_VIEW = "weekly:view"
WEEKLY_EXPORT = "weekly:export"
WEEKLY_RECTIFY = "weekly:rectify"
WEEKLY_APPROVE_RECTIFY = "weekly:approve_rectify"
WEEKLY_VIEW_PROGRESS = "weekly:view_progress"

# 月调度
MONTHLY_VIEW_REPORT = "monthly:view_report"
MONTHLY_DOWNLOAD_REPORT = "monthly:download_report"
MONTHLY_UPLOAD_REPORT = "monthly:upload_report"
MONTHLY_DELETE_REPORT = "monthly:delete_report"

# 联合巡检
JOINT_CREATE_TEMPLATE = "joint:create_template"
JOINT_PUBLISH = "joint:publish"
JOINT_SUBMIT = "joint:submit"
JOINT_VIEW = "joint:view"
JOINT_RECTIFY = "joint:rectify"
JOINT_APPROVE_RECTIFY = "joint:approve_rectify"
JOINT_APPROVE = "joint:approve"
JOINT_SIGN = "joint:sign"

# 视频巡检模块
VIDEO_WATCH = "video:watch"
VIDEO_WATCH_ALL = "video:watch_all"
VIDEO_WATCH_ASSIGNED = "video:watch_assigned"
VIDEO_CREATE_TEMPLATE = "video:create_template"
VIDEO_INSPECT = "video:inspect"
VIDEO_SNAPSHOT = "video:snapshot"
VIDEO_VIEW_RECORD = "video:view_record"
VIDEO_RECTIFY = "video:rectify"
VIDEO_APPROVE_RECTIFY = "video:approve_rectify"

# 智能设备模块
DEVICE_VIEW = "device:view"
DEVICE_ADD = "device:add"
DEVICE_EDIT = "device:edit"
DEVICE_DELETE = "device:delete"
DEVICE_VIEW_DATA = "device:view_data"
DEVICE_EXPORT_DATA = "device:export_data"

# 留样秤
SAMPLE_SCALE_VIEW = "sample_scale:view"
SAMPLE_SCALE_EXPORT = "sample_scale:export"

# 晨检仪
MORNING_CHECK_VIEW = "morning_check:view"
MORNING_CHECK_EXPORT = "morning_check:export"
MORNING_CHECK_UPDATE_EMPLOYEE = "morning_check:update_employee"

# AI行为分析
AI_BEHAVIOR_VIEW = "ai_behavior:view"
AI_BEHAVIOR_EXPORT = "ai_behavior:export"

# 留样冰箱
SAMPLE_FRIDGE_VIEW = "sample_fridge:view"
SAMPLE_FRIDGE_EXPORT = "sample_fridge:export"

# 员工管理模块
EMPLOYEE_ADD = "employee:add"
EMPLOYEE_EDIT = "employee:edit"
EMPLOYEE_DELETE = "employee:delete"
EMPLOYEE_VIEW = "employee:view"

# 仪表盘与报表模块
DASHBOARD_VIEW_REGULATOR = "dashboard:view_regulator"
DASHBOARD_VIEW_CANTEEN = "dashboard:view_canteen"
DASHBOARD_VIEW_RANK = "dashboard:view_rank"
DASHBOARD_VIEW_RISK = "dashboard:view_risk"
DASHBOARD_EXPORT = "dashboard:export"

# 系统管理模块
SYSTEM_VIEW_LOG = "system:view_log"
SYSTEM_CONFIG = "system:config"
SYSTEM_BACKUP = "system:backup"

# 权限分组
PERMISSIONS_BY_MODULE = {
    "user": [
        USER_ADD, USER_EDIT, USER_DELETE, USER_VIEW,
        USER_ASSIGN_CANTEEN, USER_ASSIGN_ROLE
    ],
    "role": [
        ROLE_ADD, ROLE_EDIT, ROLE_DELETE, ROLE_VIEW,
        ROLE_ASSIGN_PERMISSION
    ],
    "canteen": [
        CANTEEN_ADD, CANTEEN_EDIT, CANTEEN_DELETE, CANTEEN_VIEW,
        CANTEEN_ASSIGN_DEVICE, CANTEEN_ASSIGN_CAMERA
    ],
    "department": [
        DEPARTMENT_ADD, DEPARTMENT_EDIT, DEPARTMENT_DELETE, DEPARTMENT_VIEW
    ],
    "ledger": [
        LEDGER_TEMPLATE_ADD, LEDGER_TEMPLATE_EDIT, LEDGER_TEMPLATE_DELETE,
        LEDGER_TEMPLATE_VIEW, LEDGER_TEMPLATE_PUBLISH, LEDGER_ADD,
        LEDGER_EDIT, LEDGER_SUBMIT, LEDGER_VIEW, LEDGER_EXPORT,
        LEDGER_SIGN, LEDGER_UPLOAD_FILE
    ],
    "sop": [
        SOP_ADD, SOP_EDIT, SOP_DELETE, SOP_VIEW, SOP_VIEW_PROGRESS
    ],
    "inspection": [
        # 日管控
        DAILY_CREATE_TEMPLATE, DAILY_PUBLISH, DAILY_SUBMIT, DAILY_VIEW,
        DAILY_VIEW_PROGRESS, DAILY_APPROVE,
        # 周排查
        WEEKLY_CREATE_TEMPLATE, WEEKLY_PUBLISH, WEEKLY_SUBMIT, WEEKLY_VIEW,
        WEEKLY_EXPORT, WEEKLY_RECTIFY, WEEKLY_APPROVE_RECTIFY, WEEKLY_VIEW_PROGRESS,
        # 月调度
        MONTHLY_VIEW_REPORT, MONTHLY_DOWNLOAD_REPORT, MONTHLY_UPLOAD_REPORT,
        MONTHLY_DELETE_REPORT,
        # 联合巡检
        JOINT_CREATE_TEMPLATE, JOINT_PUBLISH, JOINT_SUBMIT, JOINT_VIEW,
        JOINT_RECTIFY, JOINT_APPROVE_RECTIFY, JOINT_APPROVE, JOINT_SIGN
    ],
    "video": [
        VIDEO_WATCH, VIDEO_WATCH_ALL, VIDEO_WATCH_ASSIGNED,
        VIDEO_CREATE_TEMPLATE, VIDEO_INSPECT, VIDEO_SNAPSHOT,
        VIDEO_VIEW_RECORD, VIDEO_RECTIFY, VIDEO_APPROVE_RECTIFY
    ],
    "device": [
        DEVICE_VIEW, DEVICE_ADD, DEVICE_EDIT, DEVICE_DELETE,
        DEVICE_VIEW_DATA, DEVICE_EXPORT_DATA,
        # 留样秤
        SAMPLE_SCALE_VIEW, SAMPLE_SCALE_EXPORT,
        # 晨检仪
        MORNING_CHECK_VIEW, MORNING_CHECK_EXPORT, MORNING_CHECK_UPDATE_EMPLOYEE,
        # AI行为分析
        AI_BEHAVIOR_VIEW, AI_BEHAVIOR_EXPORT,
        # 留样冰箱
        SAMPLE_FRIDGE_VIEW, SAMPLE_FRIDGE_EXPORT
    ],
    "employee": [
        EMPLOYEE_ADD, EMPLOYEE_EDIT, EMPLOYEE_DELETE, EMPLOYEE_VIEW
    ],
    "dashboard": [
        DASHBOARD_VIEW_REGULATOR, DASHBOARD_VIEW_CANTEEN,
        DASHBOARD_VIEW_RANK, DASHBOARD_VIEW_RISK, DASHBOARD_EXPORT
    ],
    "system": [
        SYSTEM_VIEW_LOG, SYSTEM_CONFIG, SYSTEM_BACKUP
    ]
}
