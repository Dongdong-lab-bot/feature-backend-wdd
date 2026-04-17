# 张子昊 - 模块一多租户拦截器进展记录
> 目标回顾：后端任意 SQL（`select/update/delete/insert`）在开发者**不写 tenant 条件**的情况下，依然被强制限定到当前登录租户；手动越权直接失败。

## 1. 本轮交付清单（做了什么）
1. **上下文基座**：`app/core/security/user_context.py` 提供 `set_current_user / require_current_tenant`，通过 `ContextVar` 确保任意线程都能拿到 `tenant_id / user_id / role_type`。
2. **统一 Session & Base**：
	- `app/db/base.py` 只保留一个 Declarative Base，杜绝多 metadata 问题；
	- `app/db/session.py` 创建 `TenantSession`，所有 FastAPI 依赖都会走这个 Session。
3. **多租户拦截器**：`app/db/tenant_interceptor.py`
	- `SELECT`：遍历最终 `FROM` 表，只要存在 `tenant_id` 列，就自动追加 `WHERE tenant_id = 当前租户`；
	- `INSERT/UPDATE/DELETE`：在 `before_flush` 校验/注入 `tenant_id`，禁止跨租户写入 or 删除；显式写其它租户直接抛 `TenantAccessError`；
	- `TenantMixin` 注册所有“租户感知”模型，方便后续模块复用。
4. **验证用例**：`backend/tests/test_tenant_interceptor.py` 新增 4 条 Pytest
	- 自动补租户字段
	- `select *` 在租户间互不泄露
	- 批量 `update` 只更新本租户
	- 手写 `tenant_id` 触发越权
5. **依赖对齐**：`backend/requirements.txt` 补齐 `sqlalchemy / fastapi / pydantic-settings / pytest` 等，保证团队一键安装即可复现。


## 2. 使用/扩展指引
1. **接入登录模块**：认证同学在中间件中调用 `set_current_user(CurrentUser(...))` 即可把真实租户写入上下文；拦截器无需修改。
2. **建新表的要求**：凡是业务表都继承 `TenantMixin`，即可自动获得 `tenant_id` 字段 + 索引 + 拦截能力。若确实是“系统级共享表”，不要继承，并在设计文档注明原因。
3. **调试技巧**：
	- 想看实际 SQL，可在 `.env` 里把 `settings.sql_echo` 设为 `True` 观察自动拼接的 `tenant_id`；
	- 需要手动模拟登录，只需在任意地方调用 `set_current_user(CurrentUser(tenant_id=?, ...))`。

## 3. 后续计划/提醒
- 等谢传宇交付 `/auth/login` + JWT 后，把请求头中的租户信息写入 `UserContext`，即可端到端完成模块一闭环。
- 若后续模块新增“跨租户只读”需求，可以在 `tenant_interceptor.py` 中增加白名单（目前全部强制 tenant 限制）。

## 4. 验收结果（自动化测试）

- 
- **总体结果**：4 个测试用例全部通过（`4 passed`）。

- **逐项清单（均通过）**：
	- `test_insert_auto_populates_tenant_id`：插入操作会自动填充 `tenant_id`，✅ PASS
	- `test_select_is_scoped_by_context`：`select *` 在不同 `tenant_id` 上返回不同集合（租户隔离），✅ PASS
	- `test_manual_tenant_override_is_rejected`：手工指定另一个 `tenant_id` 会被拦截并抛错，✅ PASS
	- `test_bulk_update_only_touches_current_tenant`：批量更新只影响当前租户的数据，✅ PASS

> 说明：测试在本地虚拟环境内执行（使用 `.venv` 中的 Python 与已安装依赖），测试代码保存在仓库 `backend/tests/test_tenant_interceptor.py`，可由任何拉取到相同代码与依赖的同事复现。

## 5. 2026-02-8 与xcy分支合并 & 功能补充（本次新增）
1. **统一上下文入口**：新增 `app/core/context.py`，所有模块使用该文件暴露的 `UserContext` 与 `tenant_var/user_var/...`；原 `app/core/security/user_context.py` 变为兼容 shim。
2. **JWT 认证闭环**：`app/main.py` 改为挂载 `AuthMiddleware`（`app/core/middleware.py`），默认解析 `Authorization: Bearer <JWT>`，校验 `sub/tenant_id/role_type/scope` 并写入 `UserContext`，同时开启 CORS；API 层 (`app/modules/user/api.py`) 提供 `/auth/login`、`/auth/refresh`、权限与用户管理接口，生成的 Token 可直接驱动多租户拦截器。
3. **用户域增强**：`app/modules/user/models.py` 统一为 `sys_*` 体系，`User` 增加 `role_type/app_client/status/updated_at`，新增 `Image` 模型；`service.py` 支持密码校验、JWT 生成、分页统计，`org_api.py`/`image_api.py` 提供组织与素材示例接口。
4. **多租户拦截器验证**：`app/db/tenant_interceptor.py` 改为直接调用 `UserContext.require_tenant_id_int()` 获取租户；`backend/tests/test_tenant_interceptor.py` 四条用例在新上下文下全部通过（`pytest backend/tests/test_tenant_interceptor.py`）。
5. **依赖与 .gitignore**：`backend/requirements.txt` 新增 `python-jose[cryptography]`、`passlib[bcrypt]`、`mysql-connector-python` 等；根目录补上 `.gitignore`，忽略虚拟环境、`__pycache__` 及项目 PDF/笔记，避免工作区被污染。

