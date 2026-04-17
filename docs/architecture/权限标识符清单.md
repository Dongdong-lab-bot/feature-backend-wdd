# 食安平台 - 权限标识符清单

**命名规范**: `模块名:操作名` (全小写)

---

## 一、用户与组织管理模块 (user)

| 权限标识符                 | 权限说明         | 适用角色                 |
| :------------------------- | :--------------- | :----------------------- |
| `user:add`               | 创建用户账号     | 监管端管理员             |
| `user:edit`              | 编辑用户信息     | 监管端管理员             |
| `user:delete`            | 删除用户账号     | 监管端管理员             |
| `user:view`              | 查看用户列表     | 监管端管理员             |
| `user:assign_canteen`    | 分配用户食堂权限 | 监管端管理员             |
| `user:assign_role`       | 分配用户角色     | 监管端管理员             |
| `role:add`               | 创建角色         | 监管端管理员             |
| `role:edit`              | 编辑角色         | 监管端管理员             |
| `role:delete`            | 删除角色         | 监管端管理员             |
| `role:view`              | 查看角色列表     | 监管端管理员             |
| `role:assign_permission` | 分配角色权限     | 监管端管理员             |
| `canteen:add`            | 创建食堂         | 监管端管理员             |
| `canteen:edit`           | 编辑食堂信息     | 监管端管理员、食堂管理员 |
| `canteen:delete`         | 删除食堂         | 监管端管理员             |
| `canteen:view`           | 查看食堂信息     | 监管端用户、食堂端用户   |
| `canteen:assign_device`  | 关联智能设备     | 监管端管理员             |
| `canteen:assign_camera`  | 关联摄像头       | 监管端管理员             |
| `department:add`         | 新增部门         | 监管端管理员             |
| `department:edit`        | 编辑部门         | 监管端管理员             |
| `department:delete`      | 删除部门         | 监管端管理员             |
| `department:view`        | 查看部门列表     | 监管端用户               |

---

## 二、数字化台账模块 (ledger)

| 权限标识符                  | 权限说明       | 适用角色               |
| :-------------------------- | :------------- | :--------------------- |
| `ledger_template:add`     | 创建台账模板   | 监管端管理员           |
| `ledger_template:edit`    | 编辑台账模板   | 监管端管理员           |
| `ledger_template:delete`  | 删除台账模板   | 监管端管理员           |
| `ledger_template:view`    | 查看台账模板   | 监管端用户、食堂端用户 |
| `ledger_template:publish` | 下发台账模板   | 监管端管理员           |
| `ledger:add`              | 填写台账       | 食堂端用户             |
| `ledger:edit`             | 编辑台账       | 食堂端用户             |
| `ledger:submit`           | 提交台账       | 食堂端用户             |
| `ledger:view`             | 查看台账记录   | 监管端用户、食堂端用户 |
| `ledger:export`           | 导出台账数据   | 监管端用户、食堂端用户 |
| `ledger:sign`             | 台账签字       | 食堂端用户             |
| `ledger:upload_file`      | 上传第三方台账 | 食堂端用户             |
| `sop:add`                 | 创建SOP任务    | 监管端管理员           |
| `sop:edit`                | 编辑SOP任务    | 监管端管理员           |
| `sop:delete`              | 删除SOP任务    | 监管端管理员           |
| `sop:view`                | 查看SOP任务    | 监管端用户、食堂端用户 |
| `sop:view_progress`       | 查看SOP进度    | 监管端用户、食堂端用户 |

---

## 三、巡检业务模块 (inspection)

### 3.1 日管控 (daily)

| 权限标识符                | 权限说明       | 适用角色               |
| :------------------------ | :------------- | :--------------------- |
| `daily:create_template` | 创建日管控模板 | 监管端管理员           |
| `daily:publish`         | 下发日管控任务 | 监管端管理员           |
| `daily:submit`          | 提交日管控报告 | 食堂端用户、监管端用户 |
| `daily:view`            | 查看日管控记录 | 监管端用户、食堂端用户 |
| `daily:view_progress`   | 查看日管控进度 | 监管端用户             |
| `daily:approve`         | 审核日管控     | 监管端管理员           |

### 3.2 周排查 (weekly)

| 权限标识符                 | 权限说明       | 适用角色               |
| :------------------------- | :------------- | :--------------------- |
| `weekly:create_template` | 创建周排查表格 | 监管端管理员           |
| `weekly:publish`         | 下发周排查任务 | 监管端管理员           |
| `weekly:submit`          | 提交周排查报告 | 监管端用户             |
| `weekly:view`            | 查看周排查记录 | 监管端用户、食堂端用户 |
| `weekly:export`          | 导出周排查数据 | 监管端用户             |
| `weekly:rectify`         | 提交整改记录   | 食堂端用户             |
| `weekly:approve_rectify` | 审核整改记录   | 监管端用户             |
| `weekly:view_progress`   | 查看周排查进度 | 监管端用户             |

### 3.3 月调度 (monthly)

| 权限标识符                  | 权限说明       | 适用角色               |
| :-------------------------- | :------------- | :--------------------- |
| `monthly:view_report`     | 查看月调度报告 | 监管端用户、食堂端用户 |
| `monthly:download_report` | 下载月调度报告 | 监管端用户             |
| `monthly:upload_report`   | 上传月调度文件 | 监管端管理员           |

### 3.4 联合巡检 (joint)

| 权限标识符                | 权限说明         | 适用角色     |
| :------------------------ | :--------------- | :----------- |
| `joint:create_template` | 创建联合巡检表格 | 监管端管理员 |
| `joint:publish`         | 下发联合巡检任务 | 监管端管理员 |
| `joint:submit`          | 提交联合巡检报告 | 监管端用户   |
| `joint:view`            | 查看联合巡检记录 | 监管端用户   |
| `joint:rectify`         | 提交整改记录     | 食堂端用户   |
| `joint:approve_rectify` | 审核整改记录     | 监管端用户   |

---

## 四、视频巡检模块 (video)

| 权限标识符                | 权限说明           | 适用角色               |
| :------------------------ | :----------------- | :--------------------- |
| `video:watch`           | 查看视频画面       | 监管端用户、食堂端用户 |
| `video:watch_all`       | 查看所有食堂视频   | 监管端管理员           |
| `video:watch_assigned`  | 查看已分配食堂视频 | 监管端用户、食堂端用户 |
| `video:create_template` | 创建视频巡检表格   | 监管端管理员           |
| `video:inspect`         | 进行视频巡检       | 监管端用户             |
| `video:snapshot`        | 视频抓拍           | 监管端用户             |
| `video:view_record`     | 查看巡检记录       | 监管端用户、食堂端用户 |
| `video:rectify`         | 提交整改记录       | 食堂端用户             |
| `video:approve_rectify` | 审核整改记录       | 监管端用户             |

---

## 五、智能设备模块 (device)

| 权限标识符             | 权限说明     | 适用角色               |
| :--------------------- | :----------- | :--------------------- |
| `device:view`        | 查看设备信息 | 监管端用户、食堂端用户 |
| `device:add`         | 添加设备     | 监管端管理员           |
| `device:edit`        | 编辑设备信息 | 监管端管理员           |
| `device:delete`      | 删除设备     | 监管端管理员           |
| `device:view_data`   | 查看设备数据 | 监管端用户、食堂端用户 |
| `device:export_data` | 导出设备数据 | 监管端用户             |

### 5.1 留样秤 (sample_scale)

| 权限标识符              | 权限说明       | 适用角色               |
| :---------------------- | :------------- | :--------------------- |
| `sample_scale:view`   | 查看留样秤记录 | 监管端用户、食堂端用户 |
| `sample_scale:export` | 导出留样秤数据 | 监管端用户             |

### 5.2 晨检仪 (morning_check)

| 权限标识符                        | 权限说明         | 适用角色               |
| :-------------------------------- | :--------------- | :--------------------- |
| `morning_check:view`            | 查看晨检记录     | 监管端用户、食堂端用户 |
| `morning_check:export`          | 导出晨检数据     | 监管端用户             |
| `morning_check:update_employee` | 更新员工晨检信息 | 食堂端用户             |

### 5.3 AI行为分析 (ai_behavior)

| 权限标识符             | 权限说明       | 适用角色               |
| :--------------------- | :------------- | :--------------------- |
| `ai_behavior:view`   | 查看AI分析记录 | 监管端用户、食堂端用户 |
| `ai_behavior:export` | 导出AI分析数据 | 监管端用户             |

### 5.4 留样冰箱 (sample_fridge)

| 权限标识符               | 权限说明     | 适用角色               |
| :----------------------- | :----------- | :--------------------- |
| `sample_fridge:view`   | 查看冰箱记录 | 监管端用户、食堂端用户 |
| `sample_fridge:export` | 导出冰箱数据 | 监管端用户             |

---

## 六、员工管理模块 (employee)

| 权限标识符          | 权限说明     | 适用角色     |
| :------------------ | :----------- | :----------- |
| `employee:add`    | 新增员工     | 食堂端管理员 |
| `employee:edit`   | 编辑员工信息 | 食堂端管理员 |
| `employee:delete` | 删除员工     | 食堂端管理员 |
| `employee:view`   | 查看员工列表 | 食堂端用户   |

---

## 七、仪表盘与报表模块 (dashboard)

| 权限标识符                   | 权限说明         | 适用角色     |
| :--------------------------- | :--------------- | :----------- |
| `dashboard:view_regulator` | 查看监管端驾驶舱 | 监管端用户   |
| `dashboard:view_canteen`   | 查看食堂端首页   | 食堂端用户   |
| `dashboard:view_rank`      | 查看食堂排名     | 监管端用户   |
| `dashboard:view_risk`      | 查看食堂风险指数 | 食堂端用户   |
| `dashboard:export`         | 导出报表数据     | 监管端管理员 |

---

## 八、系统管理模块 (system)

| 权限标识符          | 权限说明     | 适用角色     |
| :------------------ | :----------- | :----------- |
| `system:view_log` | 查看系统日志 | 监管端管理员 |
| `system:config`   | 系统配置     | 监管端管理员 |
| `system:backup`   | 数据备份     | 监管端管理员 |

---

## 权限统计

| 模块           |     权限数量 |
| :------------- | -----------: |
| 用户与组织管理 |           20 |
| 数字化台账     |           17 |
| 巡检业务       |           27 |
| 视频巡检       |            9 |
| 智能设备       |           14 |
| 员工管理       |            4 |
| 仪表盘与报表   |            5 |
| 系统管理       |            3 |
| **合计** | **99** |

---

## 使用说明

### 后端使用示例 (Python FastAPI)

```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_permission(permission: str):
    """权限装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从当前用户获取权限列表
            user_permissions = get_current_user_permissions()
            if permission not in user_permissions:
                raise HTTPException(status_code=403, detail=f"缺少权限: {permission}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.post("/ledger/add")
@require_permission("ledger:add")
async def create_ledger(data: LedgerSchema):
    """创建台账"""
    pass
```

### 前端使用示例 (Vue 3)

```typescript
// utils/permission.ts
export function hasPermission(permission: string): boolean {
  const userPermissions = useUserStore().permissions
  return userPermissions.includes(permission)
}

// 在组件中使用
<template>
  <el-button v-if="hasPermission('ledger:add')" @click="handleAdd">
    新增台账
  </el-button>
</template>

<script setup lang="ts">
import { hasPermission } from '@/utils/permission'
</script>
```

---

## 注意事项

1. **权限命名一律小写**，使用冒号分隔模块和操作
2. **新增权限流程**：前端提出 → 产品确认 → 更新本文档 → 后端实现
3. **权限粒度原则**：优先按功能操作拆分，避免过度细化导致管理复杂
4. **向后兼容**：权限标识符一旦发布，禁止修改，只能新增或废弃
