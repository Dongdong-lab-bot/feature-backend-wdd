"""数据Agent - SQL生成器（大模型通信层）

核心函数 generate_sql_with_retry：
1. 组装 System Prompt + 用户自然语言 + 表结构
2. 调用大模型生成 SQL（通过 AsyncLLMClient）
3. 剥离 Markdown 外套，提取纯净 SQL
4. 异常兜底，对齐红线要求
"""

import re
from typing import List, Dict

from src.core.config import llm_settings
from src.core.exceptions import LLMCallFailedError, LLMResponseInvalidError, LLMFuseTriggeredError
from src.core.llm_client import AsyncLLMClient
from src.core.logger import log
from src.core.schemas import SqlGenerationStatusEnum, AlertCoreModel
from .models import SQLGenerateResult


# ============================================================
# Schema 上下文生成工具
# ============================================================

def build_alert_table_schema() -> str:
    """基于 AlertCoreModel 生成告警表结构描述文本，供麦锦涛的 Handler 调用。

    返回的文本可直接作为 generate_sql_with_retry 的 schema_context 参数，
    注入到 System Prompt 的 {schema_context} 占位符位置。

    Returns:
        表名 + 所有字段名、类型、含义的格式化文本
    """
    lines = [
        "## 告警数据表 (alarms)",
        "",
        "| 字段 | 类型 | 说明 |",
        "|------|------|------|",
    ]
    for name, field in AlertCoreModel.model_fields.items():
        if name == "trace_id":
            continue
        field_type = _describe_type(field.annotation)
        description = field.description or ""
        lines.append(f"| {name} | {field_type} | {description} |")
    return "\n".join(lines)


def _describe_type(annotation) -> str:
    """将 Pydantic 字段类型转为 LLM 可读的类型描述"""
    import typing
    raw = str(annotation)
    raw = raw.replace("<class '", "").replace("'>", "").replace("<enum '", "").replace("'>", "")
    # 处理 Optional
    if "NoneType" in raw or "Optional" in raw:
        raw = raw.replace("typing.Optional[", "").rstrip("]")
        raw = raw.replace("typing.Union[", "").replace(", NoneType]", "")
        return raw.upper() + " (可选)"
    # 处理枚举
    if "Enum" in raw:
        return raw.split(".")[-1] + " (枚举)"
    # 简单类型
    type_map = {
        "str": "VARCHAR",
        "int": "INT",
        "float": "FLOAT",
        "bool": "BOOLEAN",
        "datetime.datetime": "DATETIME",
    }
    return type_map.get(raw, raw.upper())


# ============================================================
# System Prompt 模板
# {schema_context} 由调用方填充后传入
# ============================================================
_SYSTEM_PROMPT_TEMPLATE = """\
你是一个食品安全数据分析专家，擅长将自然语言问题转换为只读SQL查询语句。

## 表结构
{schema_context}

## 规则（必须严格遵守）
1. **只生成 SELECT**：禁止生成 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE 等写操作语句。
2. **单条语句**：每次只输出一条 SQL 语句，禁止多语句、禁止存储过程、禁止函数调用。
3. **必须有 WHERE**：如果查询没有过滤条件，添加合理的默认过滤（如最近7天）。
4. **禁止全表扫描**：查询必须利用索引列（id、时间戳等）限定范围。
5. **仅输出SQL**：只输出纯净的 SQL 语句，无需解释、注释、Markdown代码块标记。

## 输出格式
直接输出可执行的 SQL 语句，一行或格式化多行均可，但不要包裹任何 Markdown标记。"""


def _build_messages(user_query: str, schema_context: str) -> List[Dict[str, str]]:
    """组装大模型调用消息列表"""
    system_content = _SYSTEM_PROMPT_TEMPLATE.format(schema_context=schema_context)
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_query},
    ]


def _extract_sql_from_response(raw_response: str) -> str:
    """从大模型响应中提取纯净 SQL。

    处理三种情况：
    1. ```sql ... ``` 包裹的代码块
    2. ``` ... ``` 无语言标记的代码块
    3. 纯文本 SQL（无 Markdown 包裹）
    """
    if not raw_response:
        return ""

    text = raw_response.strip()
    if not text:
        return raw_response

    # 尝试匹配 ```sql ... ``` 或 ``` ... ```
    pattern = r"```(?:sql)?\s*\n?(.*?)\n?```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 无代码块标记，直接返回去除首尾空白后的文本
    return text


# ============================================================
# 大模型调用（异步，通过 AsyncLLMClient）
# ============================================================

async def _call_llm(messages: List[Dict[str, str]], trace_id: str = "") -> str:
    """单次异步大模型调用，返回原始响应文本。

    通过 AsyncLLMClient 发起调用，复用其内置的：
    - 指数退避重试（网络超时/限流/断连）
    - 熔断器状态管理
    - 审计日志自动埋点

    Raises:
        LLMCallFailedError: 网络错误、超时、API异常
        LLMResponseInvalidError: 响应为空或格式异常
        LLMFuseTriggeredError: 熔断器开启
    """
    async with AsyncLLMClient() as client:
        content = await client.chat(
            messages=messages,
            trace_id=trace_id,
            temperature=0.1,
            max_tokens=1024,
        )

    if not content:
        raise LLMResponseInvalidError(
            message="大模型返回内容为空",
            detail={"trace_id": trace_id},
        )

    return content


# ============================================================
# Text-to-SQL 核心入口（异步）
#
# 重试机制说明：
#   - AsyncLLMClient.chat(): 传输层重试（网络超时/限流/断连）、熔断器
#   - 本函数: 业务层重试（LLM 返回空响应/非 SQL 文本）、SQL 提取与校验
# 两者职责分离，本函数保留业务语义校验重试。
# ============================================================

async def generate_sql_with_retry(
    user_query: str,
    schema_context: str,
    trace_id: str = "",
) -> SQLGenerateResult:
    """Text-to-SQL 核心函数：自然语言 → 纯净SQL（异步）。

    流程：
    1. 组装 System Prompt + 表结构 + 用户问题
    2. 异步调用大模型，最多3次重试
    3. 剥离 Markdown 外套，提取纯净 SQL
    4. 3次全败后抛出 LLMFuseTriggeredError

    Args:
        user_query: 用户自然语言查询问题
        schema_context: 表结构 DDL / 字段说明文本（由 {{TABLE_SCHEMA}} 填充后传入）
        trace_id: 全链路追踪ID，为空则自动生成

    Returns:
        SQLGenerateResult: 包含 generated_sql、sql_generation_status、retry_count
    """
    max_retries = llm_settings.llm_max_retries
    messages = _build_messages(user_query, schema_context)
    last_error = ""

    for attempt in range(1, max_retries + 1):
        try:
            raw_response = await _call_llm(messages, trace_id)
            sql = _extract_sql_from_response(raw_response)

            if not sql or not sql.strip().upper().startswith("SELECT"):
                raise LLMResponseInvalidError(
                    message="未能从大模型响应中提取有效SQL",
                    detail={"trace_id": trace_id, "raw_response": raw_response[:200]},
                )

            log.audit(
                f"[generate_sql] 第{attempt}次成功 | "
                f"query={user_query[:80]} | sql={sql[:120]}",
                trace_id=trace_id,
            )
            return SQLGenerateResult(
                user_query=user_query,
                generated_sql=sql,
                sql_generation_status=SqlGenerationStatusEnum.SUCCESS,
                retry_count=attempt,
            )

        except Exception as exc:
            last_error = str(exc)
            log.warning(
                f"[generate_sql] 第{attempt}/{max_retries}次失败 | "
                f"error={last_error} | query={user_query[:80]}"
            )

    # 3次重试全部失败，抛出让上游熔断器感知
    log.audit(
        f"[generate_sql] 全部{max_retries}次重试失败 | "
        f"query={user_query[:80]} | last_error={last_error}",
        trace_id=trace_id,
    )
    raise LLMFuseTriggeredError(
        message=f"大模型连续{max_retries}次调用失败: {last_error}",
        detail={"trace_id": trace_id, "retry_count": max_retries, "query": user_query[:80]},
    )
