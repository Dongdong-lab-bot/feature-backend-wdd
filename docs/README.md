# 项目文档索引

> 本文档目录是项目的唯一可信来源（Single Source of Truth）

---

## 文档分类

### 📐 架构文档 (Architecture)

存放位置：[`architecture/`](./architecture/)

| 文档 | 说明 |
|------|------|
| [模块一：组织树 + 租户创建](./architecture/模块一：组织树 + 租户创建事件发布.md) | 用户模块架构设计 |
| [模块二契约](./architecture/模块二契约.md) | 数字化台账 & 视频巡检架构契约 |
| [模块三 API 契约](./architecture/模块三：巡检模块 api 契约文档.md) | 巡检业务流程 API 定义 |
| [权限标识符清单](./architecture/权限标识符清单.md) | 权限标识符完整列表 |
| [AUTH_CORE_FRONTEND_INTEGRATION.md](./architecture/AUTH_CORE_FRONTEND_INTEGRATION.md) | 认证核心与前端集成方案 |

### 🔧 后端文档 (Backend)

存放位置：[`backend/`](./backend/)

| 文档 | 说明 |
|------|------|
| [ER 图](./backend/er_diagram.md) | 数据库 ER 图设计 |
| [模块一：组织树](./backend/模块一：组织树 + 租户创建事件发布.md) | 组织树实现文档 |
| [巡检状态机与 Outbox](./backend/巡检状态机与 Outbox 对接说明.md) | 状态机与事件溯源对接 |
| [端侧鉴权与外部 IdP](./backend/端侧鉴权与外部 IdP 对接完成说明.md) | 移动端鉴权集成 |
| [zzh 后端更改](./backend/zzh 后端更改.md) | 后端实现细节记录 |

### 🎨 前端文档 (Frontend)

存放位置：[`frontend/`](./frontend/)

| 文档 | 说明 |
|------|------|
| [开发框架说明](./frontend/开发框架说明.md) | 前端开发框架指南 |
| [Layout 复用](./frontend/Layout 复用.md) | 布局组件复用方案 |
| [台账 API 接口文档](./frontend/台账 API 接口文档.md) | 台账前端 API 定义 |
| [permissions.md](./frontend/permissions.md) | 前端权限控制 |
| [Week1Mask.md](./frontend/Week1Mask.md) | 第一周开发任务清单 |

### 🎯 设计文档 (Design)

存放位置：[`design/`](./design/)

- 原型设计文件（Axure RP）

### 📱 移动端文档 (Mobile)

存放位置：[`../app-mobile/docs/`](../app-mobile/docs/)

| 文档 | 说明 |
|------|------|
| [移动端 README](../app-mobile/README.md) | 移动端开发指南 |

---

## 核心契约文档

| 文档 | 说明 |
|------|------|
| [数字化台账 API 接口契约](./数字化台账 API 接口契约文档.md) | 台账模块完整 API 定义与数据格式 |

---

## 文档规范

### 新增文档

1. 根据内容选择对应分类目录
2. 在本文档中添加索引链接
3. 使用清晰的标题和目录结构

### 文档更新

- 更新后在文档末尾记录变更历史
- 重大变更需要通知相关开发人员

### 文档废弃

- 废弃文档移至 `archive/` 目录
- 在本文档中标记为已废弃

---

## 快速导航

- 🚀 [项目根目录 README](../README.md) - 项目结构与快速开始
- 📖 [AGENTS.md](../AGENTS.md) - 开发代理指南
- 📱 [移动端文档](../app-mobile/README.md) - uni-app 开发指南
