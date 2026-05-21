"""Data Agent query-result post processor.

This module converts DB JSON rows into:
1. structured summary data for routing/frontend consumption
2. safe natural-language text for end users
3. a final DataAgentResponse aligned with the global schema contract
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
import json
from typing import Any, Callable

from pydantic import BaseModel, Field, ValidationError, field_validator

from src.core.exceptions import (
    AgentHandleFailedError,
    LLMCallFailedError,
    LLMResponseInvalidError,
    ParamError,
)
from src.core.logger import TraceContext, log, mask_sensitive_data
from src.core.schemas import (
    AuditEventTypeEnum,
    AuditLogModel,
    BEIJING_TZ,
    DataAgentResponse,
    generate_id,
)

VIOLATION_LABEL_MAP = {
    "no_mask": "未佩戴口罩",
    "no_hat": "未佩戴工作帽",
    "no_uniform": "未穿工作服",
    "rat_presence": "发现鼠患",
    "smoking": "抽烟",
}

VIOLATION_CODE_MAP = {
    "no_mask": "A01",
    "no_hat": "A02",
    "no_uniform": "A03",
    "rat_presence": "A04",
    "smoking": "A05",
}

RISK_LABEL_MAP = {
    "critical": "严重风险",
    "high": "高风险",
    "medium": "中风险",
    "low": "低风险",
    "unknown": "未知风险",
}

DEFAULT_VIOLATION_TYPE = "unknown"
DEFAULT_VIOLATION_CODE = "A00"
DEFAULT_VIOLATION_LABEL = "发现异常行为"
DEFAULT_RISK_LEVEL = "unknown"
DEFAULT_RISK_LABEL = "未知风险"
EMPTY_RESULT_TEXT = "未查询到相关告警数据。"

MESSAGE_PATTERN = re.compile(r"^\[(?P<model>[^\]]+)\]\s*检测到:\s*(?P<class_name>.+?)\s*$")
ALT_ID_PATTERN = re.compile(r"\bALT[A-Z0-9]+\b", re.IGNORECASE)
PATH_PATTERN = re.compile(r"(?:/[^\s]+)|(?:[A-Za-z]:\\[^\s]+)")
FORBIDDEN_ENUM_PATTERN = re.compile(
    r"\b(?:no_mask|no_hat|no_uniform|rat_presence|high|medium|low|critical|unknown)\b",
    re.IGNORECASE,
)


class ResultTranslateRequest(BaseModel):
    trace_id: str = Field(min_length=1)
    db_json_result: list[dict[str, Any]] = Field(default_factory=list)
    user_query: str | None = None
    original_sql: str | None = None
    execute_latency_ms: int | None = Field(default=None, ge=0)

    @field_validator("trace_id")
    @classmethod
    def validate_trace_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("trace_id 不能为空")
        return normalized


class NormalizedAlertRow(BaseModel):
    id: str | None = None
    message: str
    violation_type: str
    raw_violation_type: str
    violation_label: str
    risk_level: str
    risk_label: str
    timestamp: datetime | None = None
    timestamp_text: str | None = None
    location: str | None = None
    store_id: str | None = None
    image_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ResultTranslateResult(BaseModel):
    trace_id: str
    normalized_rows: list[NormalizedAlertRow] = Field(default_factory=list)
    structured_summary: dict[str, Any] = Field(default_factory=dict)
    translated_text: str


class TranslateDBResultTextRequest(BaseModel):
    trace_id: str = Field(min_length=1)
    db_json_result: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("trace_id")
    @classmethod
    def validate_trace_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("trace_id 不能为空")
        return normalized


class TranslateDBResultTextResponse(BaseModel):
    trace_id: str
    translated_text: str


def parse_violation_type(message: str) -> str:
    normalized = message.strip()
    match = MESSAGE_PATTERN.match(normalized)
    if match:
        class_name = match.group("class_name").strip()
        if class_name:
            return class_name
        model_name = match.group("model").strip()
        if model_name:
            return model_name
    bracket_match = re.search(r"\[(?P<model>[^\]]+)\]", normalized)
    if bracket_match:
        return bracket_match.group("model").strip() or DEFAULT_VIOLATION_TYPE
    return DEFAULT_VIOLATION_TYPE


def map_violation_label(violation_type: str) -> str:
    return VIOLATION_LABEL_MAP.get(violation_type, DEFAULT_VIOLATION_LABEL)


def map_violation_code(raw_violation_type: str) -> str:
    return VIOLATION_CODE_MAP.get(raw_violation_type, DEFAULT_VIOLATION_CODE)


def map_risk_level(level: str | None) -> tuple[str, str]:
    normalized = (level or "").strip().lower()
    if not normalized:
        return DEFAULT_RISK_LEVEL, DEFAULT_RISK_LABEL
    return normalized, RISK_LABEL_MAP.get(normalized, DEFAULT_RISK_LABEL)


def parse_timestamp(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=BEIJING_TZ)
        return value

    candidate = value.strip()
    if not candidate:
        return None

    candidate = candidate.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=BEIJING_TZ)
        return parsed
    except ValueError:
        pass

    for pattern in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(candidate, pattern)
            return parsed.replace(tzinfo=BEIJING_TZ)
        except ValueError:
            continue
    return None


def format_timestamp(value: datetime | str | None) -> str | None:
    dt = parse_timestamp(value)
    if dt is None:
        return None
    return f"{dt.month}月{dt.day}日 {dt:%H:%M}"


def normalize_db_rows(rows: list[dict[str, Any]]) -> list[NormalizedAlertRow]:
    normalized_rows: list[NormalizedAlertRow] = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ParamError(
                "数据库结果行格式非法",
                detail={"row_index": index, "row_type": type(row).__name__},
            )

        message = str(row.get("message", "")).strip()
        raw_violation_type = parse_violation_type(message)
        violation_type = map_violation_code(raw_violation_type)
        violation_label = map_violation_label(raw_violation_type)
        risk_level, risk_label = map_risk_level(row.get("level"))
        parsed_timestamp = parse_timestamp(row.get("timestamp"))

        normalized_rows.append(
            NormalizedAlertRow(
                id=_optional_str(row.get("id")),
                message=message,
                violation_type=violation_type,
                raw_violation_type=raw_violation_type,
                violation_label=violation_label,
                risk_level=risk_level,
                risk_label=risk_label,
                timestamp=parsed_timestamp,
                timestamp_text=format_timestamp(parsed_timestamp),
                location=_optional_str(row.get("location")),
                store_id=_optional_str(row.get("store_id")),
                image_url=_optional_str(row.get("image_url")),
                raw=row,
            )
        )

    return normalized_rows


def build_structured_summary(rows: list[NormalizedAlertRow]) -> dict[str, Any]:
    violation_counter = Counter(row.violation_type for row in rows)
    risk_counter = Counter(row.risk_level for row in rows)
    valid_times = [row.timestamp for row in rows if row.timestamp is not None]
    location_counter = Counter(row.location for row in rows if row.location)
    violation_label_lookup = {row.violation_type: row.violation_label for row in rows}

    violation_breakdown = [
        {
            "violation_type": violation_type,
            "violation_label": violation_label_lookup.get(violation_type, DEFAULT_VIOLATION_LABEL),
            "count": count,
        }
        for violation_type, count in violation_counter.most_common()
    ]

    risk_breakdown = [
        {
            "risk_level": risk_level,
            "risk_label": RISK_LABEL_MAP.get(risk_level, DEFAULT_RISK_LABEL),
            "count": count,
        }
        for risk_level, count in risk_counter.most_common()
    ]

    top_locations = [
        {"location": location, "count": count}
        for location, count in location_counter.most_common()
    ]

    items = [
        {
            "id": row.id,
            "message": row.message,
            "violation_type": row.violation_type,
            "raw_violation_type": row.raw_violation_type,
            "violation_label": row.violation_label,
            "risk_level": row.risk_level,
            "risk_label": row.risk_label,
            "timestamp_text": row.timestamp_text,
            "image_url": row.image_url,
            "location": row.location,
            "store_id": row.store_id,
        }
        for row in rows
    ]

    return {
        "total": len(rows),
        "violation_breakdown": violation_breakdown,
        "risk_breakdown": risk_breakdown,
        "time_range": {
            "start": min(valid_times).isoformat(timespec="seconds") if valid_times else None,
            "end": max(valid_times).isoformat(timespec="seconds") if valid_times else None,
        },
        "top_locations": top_locations,
        "items": items,
    }


def build_rule_based_fallback_text(summary: dict[str, Any]) -> str:
    total = int(summary.get("total", 0) or 0)
    if total == 0:
        return EMPTY_RESULT_TEXT

    violation_breakdown = summary.get("violation_breakdown", [])
    risk_breakdown = summary.get("risk_breakdown", [])
    top_locations = summary.get("top_locations", [])

    parts = [f"本次共查询到 {total} 条告警记录"]

    if violation_breakdown:
        top_violation = violation_breakdown[0]
        parts.append(
            f"其中{top_violation.get('violation_label', DEFAULT_VIOLATION_LABEL)}最多，共 {top_violation.get('count', 0)} 条"
        )

    if risk_breakdown:
        top_risk = risk_breakdown[0]
        parts.append(f"主要为{top_risk.get('risk_label', DEFAULT_RISK_LABEL)}")

    if top_locations:
        top_location = top_locations[0]
        location = top_location.get("location")
        if location:
            parts.append(f"主要涉及{location}")

    text = "，".join(parts) + "。"
    _ensure_text_is_safe(text)
    return text


def build_llm_summary_text(
    summary: dict[str, Any],
    trace_id: str,
    llm_callable: Callable[[dict[str, Any], str], str] | None = None,
    max_retries: int = 3,
) -> str:
    if llm_callable is None:
        raise LLMCallFailedError(
            "未配置 LLM 摘要生成器",
            detail={"trace_id": trace_id},
        )

    fact_payload = {
        "total": summary.get("total", 0),
        "top_violation": _pick_summary_field(summary.get("violation_breakdown"), "violation_label"),
        "top_violation_count": _pick_summary_field(summary.get("violation_breakdown"), "count"),
        "top_risk": _pick_summary_field(summary.get("risk_breakdown"), "risk_label"),
        "top_location": _pick_summary_field(summary.get("top_locations"), "location"),
    }

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            log.info(
                f"调用 LLM 生成查询结果摘要 | attempt={attempt} | trace_id={trace_id}"
            )
            response_text = llm_callable(fact_payload, trace_id)
            cleaned = response_text.strip()
            if not cleaned:
                raise LLMResponseInvalidError(
                    "LLM 返回空文本",
                    detail={"trace_id": trace_id, "attempt": attempt},
                )
            _ensure_text_is_safe(cleaned)
            _audit_log(
                trace_id=trace_id,
                event_type=AuditEventTypeEnum.LLM_CALL,
                action="translate_db_result_to_text.llm_call",
                success=True,
                input_data={
                    "attempt": attempt,
                    "facts": fact_payload,
                },
                output_data={"translated_text": cleaned},
            )
            return cleaned
        except LLMResponseInvalidError:
            _audit_log(
                trace_id=trace_id,
                event_type=AuditEventTypeEnum.LLM_CALL,
                action="translate_db_result_to_text.llm_call",
                success=False,
                input_data={
                    "attempt": attempt,
                    "facts": fact_payload,
                },
                output_data=None,
                error_code="2002",
                error_message="LLM 返回内容不合法",
            )
            raise
        except Exception as exc:
            last_error = exc
            log.warning(
                f"LLM 摘要生成失败，准备重试 | attempt={attempt} | trace_id={trace_id} | error={str(exc)}"
            )
            _audit_log(
                trace_id=trace_id,
                event_type=AuditEventTypeEnum.LLM_CALL,
                action="translate_db_result_to_text.llm_call",
                success=False,
                input_data={
                    "attempt": attempt,
                    "facts": fact_payload,
                },
                output_data=None,
                error_code="2001",
                error_message=str(exc),
            )

    raise LLMCallFailedError(
        "LLM 调用失败",
        detail={
            "trace_id": trace_id,
            "max_retries": max_retries,
            "last_error": str(last_error) if last_error else None,
        },
    )


def build_translated_text(
    summary: dict[str, Any],
    trace_id: str,
    llm_callable: Callable[[dict[str, Any], str], str] | None = None,
) -> str:
    fallback_text = build_rule_based_fallback_text(summary)
    try:
        return build_llm_summary_text(
            summary=summary,
            trace_id=trace_id,
            llm_callable=llm_callable,
        )
    except (LLMCallFailedError, LLMResponseInvalidError):
        _audit_log(
            trace_id=trace_id,
            event_type=AuditEventTypeEnum.LLM_FUSE_TRIGGERED,
            action="translate_db_result_to_text.error_fallback",
            success=False,
            input_data={"summary_total": summary.get("total", 0)},
            output_data={"translated_text": fallback_text},
            error_code="2003",
            error_message="LLM 摘要生成失败，已回退规则摘要",
        )
        return fallback_text


def build_empty_success_response(request: ResultTranslateRequest) -> DataAgentResponse:
    return DataAgentResponse(
        code="0000",
        message="查询成功",
        success=True,
        translated_text=EMPTY_RESULT_TEXT,
        structured_summary={
            "total": 0,
            "violation_breakdown": [],
            "risk_breakdown": [],
            "time_range": {"start": None, "end": None},
            "top_locations": [],
            "items": [],
        },
        original_sql=request.original_sql,
        execute_latency_ms=request.execute_latency_ms,
        trace_id=request.trace_id,
    )


def build_success_response(
    request: ResultTranslateRequest,
    translated_text: str,
    structured_summary: dict[str, Any],
) -> DataAgentResponse:
    return DataAgentResponse(
        code="0000",
        message="查询成功",
        success=True,
        translated_text=translated_text,
        structured_summary=structured_summary,
        original_sql=request.original_sql,
        execute_latency_ms=request.execute_latency_ms,
        trace_id=request.trace_id,
    )


def translate_query_result(
    request: ResultTranslateRequest,
    llm_callable: Callable[[dict[str, Any], str], str] | None = None,
) -> DataAgentResponse:
    TraceContext.set_trace_id(request.trace_id)
    log.info(
        f"开始执行查询结果后置处理 | trace_id={request.trace_id} | rows={len(request.db_json_result)}"
    )
    _audit_log(
        trace_id=request.trace_id,
        event_type=AuditEventTypeEnum.TOOL_CALLED,
        action="translate_query_result.start",
        success=True,
        input_data={
            "rows": len(request.db_json_result),
            "has_user_query": request.user_query is not None,
            "has_original_sql": request.original_sql is not None,
        },
        output_data=None,
    )
    try:
        if request.db_json_result == []:
            response = build_empty_success_response(request)
            _audit_log(
                trace_id=request.trace_id,
                event_type=AuditEventTypeEnum.TOOL_CALLED,
                action="translate_query_result.completed",
                success=True,
                input_data={"rows": 0},
                output_data={"total": 0, "empty_result": True},
            )
            return response

        normalized_rows = normalize_db_rows(request.db_json_result)
        structured_summary = build_structured_summary(normalized_rows)
        translated_text = build_translated_text(
            summary=structured_summary,
            trace_id=request.trace_id,
            llm_callable=llm_callable,
        )
        response = build_success_response(request, translated_text, structured_summary)
        _audit_log(
            trace_id=request.trace_id,
            event_type=AuditEventTypeEnum.TOOL_CALLED,
            action="translate_query_result.completed",
            success=True,
            input_data={"rows": len(request.db_json_result)},
            output_data={"total": structured_summary.get("total", 0)},
        )
        return response
    except ParamError as exc:
        _audit_log(
            trace_id=request.trace_id,
            event_type=AuditEventTypeEnum.TOOL_CALLED,
            action="translate_query_result.failed",
            success=False,
            input_data={"rows": len(request.db_json_result)},
            output_data=None,
            error_code=exc.error_code.value,
            error_message=exc.message,
        )
        raise
    except ValidationError as exc:
        _audit_log(
            trace_id=request.trace_id,
            event_type=AuditEventTypeEnum.TOOL_CALLED,
            action="translate_query_result.failed",
            success=False,
            input_data={"rows": len(request.db_json_result)},
            output_data=None,
            error_code="1001",
            error_message=str(exc),
        )
        raise ParamError(
            "结果转化入参校验失败",
            detail={"trace_id": request.trace_id, "error": str(exc)},
        ) from exc
    except Exception as exc:
        _audit_log(
            trace_id=request.trace_id,
            event_type=AuditEventTypeEnum.TOOL_CALLED,
            action="translate_query_result.failed",
            success=False,
            input_data={"rows": len(request.db_json_result)},
            output_data=None,
            error_code="5002",
            error_message=str(exc),
        )
        raise AgentHandleFailedError(
            "结果转化处理失败",
            detail={"trace_id": request.trace_id, "error": str(exc)},
        ) from exc


def translate_db_result_to_text(
    request: TranslateDBResultTextRequest,
    llm_callable: Callable[[dict[str, Any], str], str] | None = None,
) -> TranslateDBResultTextResponse:
    response = translate_query_result(
        ResultTranslateRequest(
            trace_id=request.trace_id,
            db_json_result=request.db_json_result,
        ),
        llm_callable=llm_callable,
    )
    return TranslateDBResultTextResponse(
        trace_id=request.trace_id,
        translated_text=response.translated_text or EMPTY_RESULT_TEXT,
    )


def _pick_summary_field(items: Any, field: str) -> Any:
    if isinstance(items, list) and items:
        head = items[0]
        if isinstance(head, dict):
            return head.get(field)
    return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _ensure_text_is_safe(text: str) -> None:
    if ALT_ID_PATTERN.search(text):
        raise LLMResponseInvalidError("摘要文本包含告警ID")
    if PATH_PATTERN.search(text):
        raise LLMResponseInvalidError("摘要文本包含路径信息")
    if FORBIDDEN_ENUM_PATTERN.search(text):
        raise LLMResponseInvalidError("摘要文本包含英文枚举值")


def _audit_log(
    trace_id: str,
    event_type: AuditEventTypeEnum,
    action: str,
    success: bool,
    input_data: dict[str, Any] | None,
    output_data: dict[str, Any] | None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    TraceContext.set_trace_id(trace_id)
    audit_log = AuditLogModel(
        trace_id=trace_id,
        audit_id=generate_id("AUD"),
        event_type=event_type,
        operator="data_agent",
        action=action,
        input_data=(
            json.dumps(mask_sensitive_data(input_data), ensure_ascii=False)
            if input_data is not None
            else None
        ),
        output_data=(
            json.dumps(mask_sensitive_data(output_data), ensure_ascii=False)
            if output_data is not None
            else None
        ),
        success=success,
        error_code=error_code,
        error_message=error_message,
    )
    log.audit(audit_log.model_dump_json())


__all__ = [
    "DEFAULT_RISK_LABEL",
    "DEFAULT_RISK_LEVEL",
    "DEFAULT_VIOLATION_CODE",
    "DEFAULT_VIOLATION_LABEL",
    "DEFAULT_VIOLATION_TYPE",
    "EMPTY_RESULT_TEXT",
    "MESSAGE_PATTERN",
    "NormalizedAlertRow",
    "RISK_LABEL_MAP",
    "ResultTranslateRequest",
    "ResultTranslateResult",
    "TranslateDBResultTextRequest",
    "TranslateDBResultTextResponse",
    "VIOLATION_CODE_MAP",
    "VIOLATION_LABEL_MAP",
    "_audit_log",
    "build_empty_success_response",
    "build_llm_summary_text",
    "build_rule_based_fallback_text",
    "build_structured_summary",
    "build_success_response",
    "build_translated_text",
    "format_timestamp",
    "map_risk_level",
    "map_violation_code",
    "map_violation_label",
    "normalize_db_rows",
    "parse_timestamp",
    "parse_violation_type",
    "translate_db_result_to_text",
    "translate_query_result",
]
