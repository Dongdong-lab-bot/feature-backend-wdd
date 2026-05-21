# SQL Generator — 大模型通信与结果转化

**所属组**：B组 — 数据分析Agent组  
**负责人**：许嘉祺（模型工程研发）  
**模块**：模块二：大模型通信与结果转化  
**状态**：Week 1 MVP，Mock 环境验证阶段  

---

## 一、定位

`generate_sql_with_retry` 是 Text-to-SQL 链路的最上游环节——将用户的自然语言问题 + 表结构 Schema 发给大模型，提取纯净 SQL 语句返回。

在整个数据 Agent 全链路中的位置：

```
用户自然语言 → [你在这里] → AST安全校验 → AST性能校验 → DB执行 → 结果翻译
           generate_sql  柴文烨         甘勇辉       柯泽裕    黄柏杨
```

**核心职责**：
1. 组装 System Prompt + 表结构 + 用户问题
2. 调用大模型生成 SQL
3. 剥离 Markdown 外套，提取纯净 SQL
4. 超时重试（3 次）+ 异常兜底

---

## 二、文件清单

| 文件 | 职责 |
|------|------|
| `src/agents/data_agent/models.py` | Pydantic 数据模型（`TraceBase`, `SQLGenerateRequest`, `SQLGenerateResult`） |
| `src/agents/data_agent/sql_generator.py` | 核心实现（System Prompt、SQL提取器、大模型调用、重试主函数） |
| `tests/test_sql_generator.py` | 17 个单元测试（16 passed, 1 skipped） |

---

## 三、设计依据（规范引用）

| 规范文档 | 版本 | 引用章节 | 与本模块的关系 |
|----------|------|---------|---------------|
| `全局schema规范草案.md` | V1.1 | Section 2.1 TraceBase | `SQLGenerateResult` 继承 `TraceBase`，获得 32 位 hex `trace_id` |
| `全局schema规范草案.md` | V1.1 | Section 6.2 SQLGenerateResult | 返回模型字段名、类型、状态字符串 **完全一致** |
| `全局schema规范草案.md` | V1.1 | Section 1.3 敏感信息脱敏 | 审计日志导入 `mask_sensitive_data`，禁止明文落库 |
| `全局schema规范草案.md` | V1.1 | Section 2.3 错误码（30xx） | 使用 `LLMCallFailedError`(2001)、`LLMResponseInvalidError`(2002)、`LLMFuseTriggeredError`(2003) |
| `全局schema规范草案.md` | V1.1 | Section 7 审计日志 | 每次 LLM 调用通过 `log.audit()` 全量留痕 |
| `api和字段契约.pdf` | Week1 架构审查纠偏版 | Section 贰-内部组件一 | 函数签名、入参出参、Pydantic 模型定义 |
| `api和字段契约.pdf` | Week1 架构审查纠偏版 | Section 陆 内部组件接口标准化 | 入参出参必须定义 Pydantic 模型，与全局 Schema 对齐 |
| `任务分配.pdf` | Week1 架构审查纠偏版 | Page 2 许嘉祺 | 任务定义：大模型 API 通信、异常兜底、Markdown 剥离 |
| `研发流程.md` | V1.0 | B组职责 | Text-to-SQL 核心引擎开发，数据 Agent 组内规范 |
| `简要规划.md` | — | 数据处理Agent 优化建议 | 权限最小化、操作全链路审计、核心数据容灾 |

---

## 四、数据模型

### 4.1 TraceBase

> 引用规范：`全局schema规范草案.md` Section 2.1

```python
class TraceBase(BaseModel):
    trace_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        min_length=32,
        max_length=32,
    )
```

**说明**：当前在 `data_agent/models.py` 中临时定义。待基建组发布 `src/core/schemas.py` 后，替换为全局导入。

### 4.2 SQLGenerateRequest（入参）

> 引用规范：`api和字段契约.pdf` Section 贰-内部组件一

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_query` | `str` | 是 | 用户自然语言查询问题 |
| `schema_context` | `str` | 是 | 表结构上下文，由 `{{TABLE_SCHEMA}}` 占位符填充后的 DDL / 字段说明 |
| `trace_id` | `str` | 否 | 全链路追踪 ID，为空则结果模型中自动生成 |

### 4.3 SQLGenerateResult（出参）

> 引用规范：`全局schema规范草案.md` Section 6.2

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `trace_id` | `str` | 自动生成 | 继承自 `TraceBase`，32 位 hex UUID |
| `user_query` | `str` | — | 回显原始用户问题，用于审计追溯 |
| `generated_sql` | `str` | `""` | 生成的纯净 SQL 语句（无 Markdown 包裹） |
| `sql_generation_status` | `str` | `"retry_exhausted"` | 四态之一（见下） |
| `error_message` | `Optional[str]` | `None` | 失败时的人类可读错误描述 |
| `retry_count` | `int` | `0` | 已重试次数（含成功的当次），范围 1–3 |

**`sql_generation_status` 状态机**：

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `success` | SQL 生成成功 | LLM 返回了有效的 SELECT 语句 |
| `empty_response` | 无法提取有效 SQL | LLM 返回的文本中未包含可提取的 SQL |
| `parse_error` | 响应格式异常 | LLM 返回内容为空或格式无法解析 |
| `retry_exhausted` | 3 次重试全部失败 | 兜底状态，`generated_sql` 为空，`error_message` 包含最后失败原因 |

---

## 五、核心函数

### 5.1 generate_sql_with_retry — 主入口

```python
def generate_sql_with_retry(
    user_query: str,
    schema_context: str,
    trace_id: str = "",
) -> SQLGenerateResult:
```

**功能**：Text-to-SQL 核心函数，自然语言 → 纯净 SQL。

**流程**：
1. 调用 `_build_messages` 组装 System Prompt + 表结构 + 用户问题
2. 循环最多 3 次：
   - 调用 `_call_llm` 请求大模型
   - 调用 `_extract_sql_from_response` 剥离 Markdown 提取 SQL
   - 校验 SQL 有效且以 SELECT 开头
   - 成功 → 返回 `SQLGenerateResult(status="success")`
   - 失败 → `log.warning()` 记录后重试
3. 3 次全败 → 返回 `SQLGenerateResult(status="retry_exhausted")` 兜底

**重试次数来源**：`src/core/config.py` 的 `llm_settings.llm_max_retries`（默认 3）。

**审计日志**：每次成功和全部失败均通过 `log.audit()` 记录（对齐 `全局schema规范草案.md` Section 7）。

**使用示例**：

```python
from src.agents.data_agent import generate_sql_with_retry

result = generate_sql_with_retry(
    user_query="昨天徐汇店有多少次未戴口罩违规？",
    schema_context="CREATE TABLE mock_alarms (id VARCHAR PRIMARY KEY, ...)",
    trace_id="test-001",
)

if result.sql_generation_status == "success":
    print(f"生成的SQL: {result.generated_sql}")
    print(f"重试次数: {result.retry_count}")
else:
    print(f"失败: {result.error_message}")
```

### 5.2 _call_llm — 大模型调用

```python
def _call_llm(messages: List[Dict[str, str]], trace_id: str = "") -> str:
```

**功能**：通过 OpenAI SDK 发起单次大模型调用。

**配置来源**（全部来自 `src/core/config.py` 的 `llm_settings` 单例）：

| 参数 | 配置项 | 默认值 | 说明 |
|------|--------|--------|------|
| `base_url` | `llm_base_url` | `""` | 大模型 API 地址 |
| `api_key` | `llm_api_key` | `None` | API 密钥 |
| `model` | `llm_model_name` | `""` | 模型名称 |
| `timeout` | `llm_timeout` | 60s | 调用超时 |
| `temperature` | 硬编码 | 0.1 | 低温度保证 SQL 确定性 |
| `max_tokens` | 硬编码 | 1024 | SQL 语句不需要太长 |

**异常映射**：

| 场景 | 异常类型 | 错误码 |
|------|---------|--------|
| 网络错误/超时/API 异常 | `LLMCallFailedError` | 2001 |
| 响应无 choices | `LLMResponseInvalidError` | 2002 |
| 响应内容为空 | `LLMResponseInvalidError` | 2002 |

所有异常类型定义于 `src/core/exceptions.py`，错误码对齐 `全局schema规范草案.md` Section 2.3。

### 5.3 _extract_sql_from_response — SQL 提取

```python
def _extract_sql_from_response(raw_response: str) -> str:
```

**功能**：从大模型原始响应中剥离 Markdown 代码块标记，返回纯净 SQL。

**处理规则**（正则 ` ```(?:sql)?\s*\n?(.*?)\n?``` `）：

| 输入 | 输出 |
|------|------|
| `` ````sql\nSELECT * FROM alarms\n```` `` | `SELECT * FROM alarms` |
| `` ````\nSELECT COUNT(*) FROM alarms\n```` `` | `SELECT COUNT(*) FROM alarms` |
| `SELECT * FROM alarms WHERE level='high'` | `SELECT * FROM alarms WHERE level='high'` |
| 有前导文字的代码块 | 提取第一个代码块内容 |
| 多个代码块 | 只取第一个 |
| 空字符串 | `""` |

### 5.4 _build_messages — 消息组装

```python
def _build_messages(user_query: str, schema_context: str) -> List[Dict[str, str]]:
```

**功能**：将 System Prompt 模板中的 `{schema_context}` 填充后，与用户问题组装为 OpenAI Chat API 标准消息格式。

**System Prompt 包含的 5 条红线规则**：
1. 只生成 SELECT — 禁止 INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE
2. 单条语句 — 禁止多语句、禁止存储过程、禁止函数调用
3. 必须有 WHERE — 无过滤条件时默认加近 7 天
4. 禁止全表扫描 — 必须利用索引列
5. 仅输出 SQL — 无需解释、注释、Markdown 标记

---

## 六、依赖关系

```
src/agents/data_agent/sql_generator.py
├── openai (SDK 2.6.1)              # 大模型 API 通信
├── src/core/config.py              # llm_settings (base_url/api_key/model/timeout/retries)
├── src/core/exceptions.py          # LLMCallFailedError, LLMResponseInvalidError
├── src/core/logger.py              # log.audit(), log.warning(), mask_sensitive_data
└── src/agents/data_agent/models.py # SQLGenerateResult, TraceBase
```

---

## 七、跨组协同与对接接口

### 7.1 对接总览

```
                     ┌──────────────────────┐
                     │    许嘉祺（本模块）     │
                     │  generate_sql_with_   │
                     │  retry()              │
                     └──┬──┬──┬────────┬────┘
                        │  │  │        │
        ┌───────────────┘  │  │        └───────────────┐
        ↓                  ↓  ↓                        ↓
   ┌─────────┐  ┌──────────┐ ┌──────────┐  ┌──────────────┐
   │基建组    │  │柯泽裕     │ │眭子墨     │  │麦锦涛          │
   │schemas  │  │假表DDL   │ │Prompt    │  │集成入口        │
   │SDK      │  │          │ │调优      │  │standard_       │
   │         │  │          │ │          │  │response       │
   └─────────┘  └──────────┘ └──────────┘  └──────────────┘
```

### 7.2 对接点①：柯泽裕 — Schema 上下文输入

**涉及文件**：`src/agents/data_agent/sql_generator.py`

**对接方式**：柯泽裕提供假表 DDL 文本 → 作为 `schema_context` 参数传入 `generate_sql_with_retry()`

```python
# 柯泽裕的假表 DDL 示例（来自他本地 Mock 环境）
schema_ddl = """
CREATE TABLE mock_alarms (
    id VARCHAR PRIMARY KEY,
    camera_id VARCHAR NOT NULL,
    camera_name VARCHAR(100),
    location VARCHAR(100),
    violation_type VARCHAR(10),
    level VARCHAR(10),
    confidence FLOAT,
    image_url VARCHAR(200),
    is_verified BOOLEAN,
    timestamp DATETIME,
    store_name VARCHAR(50)
);
"""

# 传入本模块
result = generate_sql_with_retry(
    user_query=user_question,
    schema_context=schema_ddl,   # ← 对接点：柯泽裕产出
    trace_id=trace_id,
)
```

**当前状态**：函数已就绪，等待柯泽裕提供假表 DDL（Week1 Day2 前）。

**对接验证**：假表 DDL 拿到后，替换上文 8.2 冒烟测试中的 `schema_context`，重新跑一次 `generate_sql_with_retry`，确认 LLM 生成的 SQL 引用了正确的字段名。

---

### 7.3 对接点②：麦锦涛 — 场景处理器集成

**涉及文件**：
- 麦锦涛侧：`BaseSceneHandler` / `AlarmQueryHandler` / `DataAgent` 统一入口
- 本模块侧：`src/agents/data_agent/sql_generator.py:generate_sql_with_retry()`

**对接方式**：麦锦涛的 `AlarmQueryHandler.handle()` 调用本模块函数，组装 Text-to-SQL 全链路。

```python
# 麦锦涛的 AlarmQueryHandler.handle() 中将调用：
from src.agents.data_agent import generate_sql_with_retry, SQLGenerateResult

def handle(self, user_query: str, context: HandlerContext) -> dict:
    # 1. 调用本模块（许嘉祺）
    sql_result: SQLGenerateResult = generate_sql_with_retry(
        user_query=user_query,
        schema_context=self._get_schema_context(),  # 从柯泽裕处获取
        trace_id=context.trace_id,
    )

    if sql_result.sql_generation_status != "success":
        return standard_response(
            DataAgentErrorCode.LLM_CALL_FAILED,
            "", sql_result.error_message, context.trace_id,
        )

    # 2. AST 安全校验（柴文烨）
    # 3. AST 性能校验（甘勇辉）
    # 4. DB 执行（柯泽裕）
    # 5. 结果翻译（黄柏杨）
    ...
```

**麦锦涛需要知道的字段**：

| 字段 | 用途 |
|------|------|
| `sql_result.generated_sql` | 传给下游 AST 校验 → DB 执行 |
| `sql_result.sql_generation_status` | 判断是否需要走兜底逻辑 |
| `sql_result.error_message` | 兜底时返回给用户的错误提示 |
| `sql_result.trace_id` | 贯穿全链路的追踪 ID |
| `sql_result.retry_count` | 审计用，记录 LLM 重试情况 |

**当前状态**：函数已就绪，`__init__.py` 已导出 `generate_sql_with_retry`。等待麦锦涛 Week1 Day4 前集成。

---

### 7.4 对接点③：眭子墨 — System Prompt 协同

**涉及文件**：`src/agents/data_agent/sql_generator.py:_SYSTEM_PROMPT_TEMPLATE`

**对接方式**：
- 眭子墨负责 `{{TABLE_SCHEMA}}` 占位符体系 + Prompt 框架
- 本模块的 `_SYSTEM_PROMPT_TEMPLATE` 使用 `{schema_context}` 占位符（运行时由 `_build_messages` 填充）
- 两者格式一致，后续眭子墨优化 Prompt 后直接替换 `_SYSTEM_PROMPT_TEMPLATE` 字符串即可

**对接位置**：`sql_generator.py` 第 22-36 行。

**待协作事项**：
1. 根据真实 LLM 测试结果，在 Prompt 中声明数据库类型（MySQL 8.0 vs SQLite）
2. 补充违规类型枚举的具体值（如 `A01=未戴口罩`），帮助 LLM 做精确匹配
3. 增加 Few-shot 示例提升 SQL 准确率

**当前状态**：Prompt 模板已就绪，Week1 内部对齐后微调。

---

### 7.5 对接点④：基建组 — TraceBase / SDK 迁移

#### 7.5.1 TraceBase 迁移

**涉及文件**：`src/agents/data_agent/models.py` 第 17-24 行

**迁移方式**：基建组发布 `src/core/schemas.py` 后，替换两行 import：

```python
# 当前（Week1 临时）
# 在 models.py 中自定义 TraceBase

# 迁移后
from src.core.schemas import TraceBase
```

`SQLGenerateResult` 继承 `TraceBase` 不变，下游代码零改动。

#### 7.5.2 大模型统一 SDK 迁移

**涉及文件**：`src/agents/data_agent/sql_generator.py:_call_llm()` 第 77-116 行

**迁移方式**：基建组 SDK 发布后，替换 `_call_llm` 内部实现，函数签名保持不变：

```python
def _call_llm(messages: List[Dict[str, str]], trace_id: str = "") -> str:
    # 当前：openai SDK 直接调用
    # 迁移后：调用基建组统一SDK
    # from src.core.llm_client import unified_llm_call
    # return unified_llm_call(messages=messages, trace_id=trace_id)
```

主函数 `generate_sql_with_retry` 不感知内部变化，无需改动。

**当前状态**：两处均已做好接口隔离，等待基建组发布后替换。

---

## 八、测试

### 8.1 单元测试（Mock）

```bash
python -m pytest tests/test_sql_generator.py -v
```

**结果**：

```
tests/test_sql_generator.py::TestExtractSQL::test_extract_sql_block_with_language PASSED
tests/test_sql_generator.py::TestExtractSQL::test_extract_sql_block_without_language PASSED
tests/test_sql_generator.py::TestExtractSQL::test_extract_plain_sql_no_fences PASSED
tests/test_sql_generator.py::TestExtractSQL::test_extract_sql_with_leading_text PASSED
tests/test_sql_generator.py::TestExtractSQL::test_extract_sql_multiple_fences_takes_first PASSED
tests/test_sql_generator.py::TestExtractSQL::test_extract_empty_string PASSED
tests/test_sql_generator.py::TestExtractSQL::test_extract_whitespace_only PASSED
tests/test_sql_generator.py::TestBuildMessages::test_includes_system_prompt PASSED
tests/test_sql_generator.py::TestBuildMessages::test_includes_user_query PASSED
tests/test_sql_generator.py::TestBuildMessages::test_schema_placeholder_injected PASSED
tests/test_sql_generator.py::TestGenerateSQLWithRetry::test_returns_sql_on_first_success PASSED
tests/test_sql_generator.py::TestGenerateSQLWithRetry::test_preserves_input_user_query_in_result PASSED
tests/test_sql_generator.py::TestGenerateSQLWithRetry::test_retries_on_failure_then_succeeds PASSED
tests/test_sql_generator.py::TestGenerateSQLWithRetry::test_fallback_after_3_failures PASSED
tests/test_sql_generator.py::TestGenerateSQLWithRetry::test_retry_on_empty_sql_response PASSED
tests/test_sql_generator.py::TestGenerateSQLWithRetry::test_status_empty_response_when_no_sql_extractable PASSED
tests/test_sql_generator.py::TestSmokeWithRealLLM::test_real_llm_generates_select SKIPPED

======================== 16 passed, 1 skipped in 0.42s ========================
```

**测试覆盖矩阵**：

| 测试类 | 用例数 | 结果 | 覆盖 |
|--------|--------|------|------|
| `TestExtractSQL` | 7 | 7 passed | ` ```sql ``` ` 包裹、无语言标记、纯文本、前导文字、多代码块取首、空字符串、纯空白 |
| `TestBuildMessages` | 3 | 3 passed | System Prompt 包含 schema、用户问题注入、schema 占位符替换 |
| `TestGenerateSQLWithRetry` | 6 | 6 passed | 首次成功、用户查询回显、失败后重试成功、3 次全败兜底、空响应重试、非 SQL 响应消耗完重试 |
| `TestSmokeWithRealLLM` | 1 | 1 skipped | 真实 LLM 端到端（需配置 API Key 后手动执行） |

---

### 8.2 真实 LLM 冒烟测试

**配置**：DeepSeek V4 Flash，`.env` 中配置 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL_NAME`。

**输入**：

```python
result = generate_sql_with_retry(
    user_query="昨天徐汇店有多少次未戴口罩的告警？",
    schema_context="""
        CREATE TABLE mock_alarms (
            id VARCHAR PRIMARY KEY,
            camera_id VARCHAR NOT NULL,
            violation_type VARCHAR(10),
            level VARCHAR(10),
            confidence FLOAT,
            timestamp DATETIME,
            store_name VARCHAR(50)
        );
    """,
    trace_id="smoke-002",
)
```

**输出**：

```
状态: success
重试次数: 1
trace_id: f21250021b3c4cb78373c15baff20ab3
```

**生成的 SQL**：

```sql
SELECT COUNT(*) AS alarm_count
FROM mock_alarms
WHERE store_name = '徐汇'
  AND violation_type = '未戴口罩'
  AND DATE(timestamp) = DATE('now', '-1 day')
```

**验证结论**：

| 检查项 | 结果 |
|--------|------|
| `sql_generation_status == "success"` | ✅ |
| `retry_count == 1`（一次调用即成功） | ✅ |
| SQL 为 SELECT 语句（非写操作） | ✅ |
| SQL 引用正确的表名 `mock_alarms` | ✅ |
| "昨天" 被正确翻译为日期过滤条件 | ✅ |
| "徐汇店" 被正确翻译为 `store_name = '徐汇'` | ✅ |
| "未戴口罩" 被正确翻译为 `violation_type` 过滤 | ✅ |
| "有多少次" 被正确翻译为 `COUNT(*)` | ✅ |
| 审计日志 `log.audit()` 正常写入 | ✅ |

> **已知小问题**：`DATE('now', '-1 day')` 是 SQLite 语法。若生产数据库为 MySQL，需在 System Prompt 中声明数据库类型（如 "MySQL 8.0"），使 LLM 输出 `CURDATE() - INTERVAL 1 DAY`。这是 Prompt 层面的微调，代码无需改动。

---

## 九、后续迭代

1. **基建组 SDK 替换**：接到基建组发布的大模型统一调用 SDK 后，替换 `_call_llm` 内部实现（接口不变）
2. ~~**`TraceBase` 迁移**~~（已完成，见下方 4.28 更新记录）
3. ~~**`__init__.py` 补全**~~（已完成，`generate_sql_with_retry` 已加入导出）
4. **`mask_sensitive_data` 实际调用**：当前已导入，后续审计日志落库时对 `user_query` 做脱敏
5. **Prompt 迭代**：与眭子墨协作，根据真实 LLM 测试结果优化 System Prompt 规则

---

## 十、更新记录

---

### 2026-04-28 — 适配基建组全局 Schema V1.4

**触发原因**：基建组发布 `src/core/schemas.py`（V1.4），`docs/4.28/` 同步更新全局规范文档。

**改动内容**：

| 文件 | 改动 | 说明 |
|------|------|------|
| `src/agents/data_agent/models.py` | 删除本地 `TraceBase`，改为 `from src.core.schemas import TraceBase` | 基建组 schemas.py 已发布，不再需要临时定义 |
| `src/agents/data_agent/models.py` | `sql_generation_status` 类型从 `str` 升级为 `SqlGenerationStatusEnum` | 对齐全局 Schema V1.4 强约束枚举 |
| `src/agents/data_agent/sql_generator.py` | 导入 `SqlGenerationStatusEnum`，状态赋值改用枚举值 | `"success"` → `SqlGenerationStatusEnum.SUCCESS` 等 |
| `tests/test_sql_generator.py` | 断言中的字符串比较改为枚举比较 | 与生产代码类型一致 |

**新增基建依赖**（从 `origin/main` 合并）：

| 新增文件 | 与本模块的关系 |
|----------|---------------|
| `src/core/schemas.py` | 提供 `TraceBase`、`SqlGenerationStatusEnum`、所有全局枚举和数据模型 |
| `src/agents/base_agent.py` | Agent 基类（后续 DataAgent 继承用，Week1 暂不改造） |
| `src/core/exceptions.py`（+69行） | 新增 600x/700x/800x 错误码，本模块已用的 200x 不变 |
| `src/core/event_protocol.py` | Agent 间通信事件协议 |
| `src/core/message_bus.py` | 消息总线 |

**规范文档更新**（`docs/4.28/`）：

| 新文档 | 与旧版差异 | 对本模块影响 |
|--------|-----------|-------------|
| `全局schema规范草案(1).md` V1.4 | 新增 `SqlGenerationStatusEnum` 等 5 个枚举，时间字段收敛为 `created_at`/`updated_at` | `sql_generation_status` 必须用枚举 |
| `新api和字段契约.md` | 与旧 `api和字段契约.pdf` 内容一致，仅 markdown 化 | 无影响，函数签名不变 |
| `告警数据格式(1).md` | 新增，YOLO 告警原始数据格式详解 | 了解即可，不直接影响本模块 |
| `API接口契约文档.md` | 新增 | 了解即可 |
| `Agent开发规范.md` | 新增 | 后续 DataAgent 继承 BaseAgent 时参考 |
| `全局JSON-Schema规范.md` | 新增（V1.0 正式版） | 权威参考，优先级高于草案 |

**测试验证**：合并后 16 passed, 1 skipped，枚举迁移无误。
