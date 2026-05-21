# SQL 安全校验规则说明

文件：`src/agents/data_agent/sql_validator/security_check.py`
错误码：3001 `SQL_SECURITY_BLOCKED`（见 `docs/全局JSON-Schema规范.md §2.4 / §6.3`）

规则为安全红线，不对外提供配置接口。

---

| 规则编号 | 拦截目标 | 禁止原因 |
|----------|---------|---------|
| RULE-S001 | 多条 SQL（分号分隔） | 防止攻击者在合法查询后追加破坏性语句 |
| RULE-S002 | INSERT / UPDATE / DELETE / MERGE | 系统仅提供只读数据查询，禁止任何写操作 |
| RULE-S003 | CREATE / DROP / ALTER / TRUNCATE | 禁止结构变更或数据清空 |
| RULE-S004 | CALL / 未识别命令（sqlglot Command） | 禁止调用存储过程或执行 sqlglot 无法解析的原始命令 |
| RULE-S005 | COMMIT / ROLLBACK / BEGIN | 禁止手动控制事务边界 |
| RULE-S006 | GRANT / REVOKE | 禁止权限变更 |
| RULE-S007 | 非 SELECT / WITH(CTE) 的一切顶层语句 | 白名单兜底，前六条未覆盖的未知语句类型一律拒绝 |

---

**实现说明**

- RULE-S004 同时兜底了 sqlglot 将 GRANT/CALL 等解析为 `Command` 的场景，S005/S006 覆盖 sqlglot 能原生识别该类型的版本。
- `_DDL_TYPES` 中 `Alter`/`TruncateTable` 通过 `getattr` 引用，兼容低版本 sqlglot 节点缺失。
- 解析失败（空 SQL、语法错误）由 `parse_sql_ast()` 抛出 `ParamError(1001)`，本模块透传不捕获。
