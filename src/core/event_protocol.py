"""
Agent 间通信接口规范 (event_protocol.py)

定义消息总线（Redis Streams）上的事件通信协议，包括：
- 事件类型与流转方向
- 各事件类型的 Payload Schema
- 生产者/消费者映射
- 错误处理与重试策略
- 安全与权限要求

本规范为 Agent 间异步通信的唯一标准，禁止业务 Agent 直接使用底层 Redis API。
所有通信必须通过 MessageBus（src/core/message_bus.py）进行。

规范来源: docs/全局schema规范草案.md V1.4
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# =============================================================================
# 1. 通信拓扑
# =============================================================================

"""
通信拓扑图（简化版）:

    EdgeAgent
        │ HTTP POST /api/v1/alerts
        ▼
    ┌──────────────┐
    │   基建网关    │ ──[ALERT_RECEIVED]──► 消息总线
    └──────────────┘
        │
        │ 消费以下事件:
        │   RECTIFICATION_UPDATED → 同步状态到前端
        │
        ▼
    ┌──────────────┐
    │  监管 Agent   │ ──[ALERT_VERIFIED]──► 消息总线
    │  (triage)     │ ◄──[ALERT_DISPATCHED]── 消息总线
    └──────────────┘
        │
        ▼
    ┌──────────────┐
    │  数据 Agent   │ ──[SQL_GENERATED, SQL_EXECUTED, SQL_BLOCKED]──► 消息总线
    │  (data)       │ ◄──[ROUTE_DISPATCHED]── 消息总线
    └──────────────┘
        │
        ▼
    ┌──────────────┐
    │  路由 Agent   │ ──[INTENT_RECOGNIZED, ROUTE_DISPATCHED, ROUTE_COMPLETED]──► 消息总线
    │  (router)     │ ◄──[USER_QUERY_RECEIVED, USER_CONFIRMED, USER_REJECTED]── 消息总线
    └──────────────┘
        │
        ▼
    前端 (WebSocket)
"""

# =============================================================================
# 2. 事件类型总表
# =============================================================================

EVENT_TYPE_DEFINITIONS: List[Dict[str, Any]] = [
    # ── 告警业务流转 ──
    {
        "event_type": "ALERT_RECEIVED",
        "description": "网关收到边缘告警，已解析并入库",
        "producer": "infra",
        "consumers": ["triage_agent"],
        "priority": 1,
        "payload_schema": "AlertCoreModel",
        "retry_policy": "无重试（单次投递）",
    },
    {
        "event_type": "ALERT_DEDUPED",
        "description": "时空去重判定完成",
        "producer": "triage_agent",
        "consumers": ["triage_agent"],
        "priority": 2,
        "payload_schema": "{ alert_id, dedup_result, kept_alert_id, dropped_alert_ids }",
        "retry_policy": "无重试",
    },
    {
        "event_type": "ALERT_DISPATCHED",
        "description": "告警下发至监管 Agent（去重后触发 VLM 校验）",
        "producer": "triage_agent",
        "consumers": ["triage_agent"],
        "priority": 1,
        "payload_schema": "AlertCoreModel",
        "retry_policy": "无重试",
    },
    {
        "event_type": "ALERT_VERIFIED",
        "description": "VLM 校验完成（成功或否决均触发）",
        "producer": "triage_agent",
        "consumers": ["infra", "data_agent", "router_agent"],
        "priority": 1,
        "payload_schema": "ViolationEventModel",
        "retry_policy": "无重试",
    },

    # ── LLM/VLM 校验 ──
    {
        "event_type": "VERIFY_COMPLETED",
        "description": "二次校验完成",
        "producer": "triage_agent",
        "consumers": ["triage_agent"],
        "priority": 2,
        "payload_schema": "{ alert_id, event_id, verify_result, latency_ms }",
        "retry_policy": "无重试",
    },
    {
        "event_type": "VERIFY_FAILED",
        "description": "二次校验失败/异常（VLM 熔断、超时、解析失败）",
        "producer": "triage_agent",
        "consumers": ["triage_agent", "infra"],
        "priority": 1,
        "payload_schema": "{ alert_id, error_code, error_message, retry_count }",
        "retry_policy": "最多重试 3 次，超出后降级为 edge_rule",
    },

    # ── 数据查询 ──
    {
        "event_type": "SQL_GENERATED",
        "description": "Text-to-SQL 生成完成",
        "producer": "data_agent",
        "consumers": ["data_agent"],
        "priority": 2,
        "payload_schema": "SQLGenerateResult",
        "retry_policy": "无重试",
    },
    {
        "event_type": "SQL_EXECUTED",
        "description": "SQL 执行完成",
        "producer": "data_agent",
        "consumers": ["data_agent", "router_agent"],
        "priority": 2,
        "payload_schema": "DBExecuteResult",
        "retry_policy": "无重试",
    },
    {
        "event_type": "SQL_BLOCKED",
        "description": "AST 拦截触发",
        "producer": "data_agent",
        "consumers": ["data_agent", "router_agent", "infra"],
        "priority": 1,
        "payload_schema": "ASTSecurityCheckResult 或 ASTPerformanceCheckResult",
        "retry_policy": "无重试",
    },

    # ── 意图与路由 ──
    {
        "event_type": "INTENT_RECOGNIZED",
        "description": "意图识别完成",
        "producer": "router_agent",
        "consumers": ["router_agent"],
        "priority": 2,
        "payload_schema": "IntentRecognitionResult",
        "retry_policy": "无重试",
    },
    {
        "event_type": "ROUTE_DISPATCHED",
        "description": "路由分发已下发至目标 Agent",
        "producer": "router_agent",
        "consumers": ["data_agent", "triage_agent"],
        "priority": 1,
        "payload_schema": "{ session_id, plan_id, target_agent, intent_type, tool_args }",
        "retry_policy": "最多重试 3 次",
    },
    {
        "event_type": "ROUTE_COMPLETED",
        "description": "路由计划执行完成",
        "producer": "router_agent",
        "consumers": ["infra"],
        "priority": 2,
        "payload_schema": "{ session_id, plan_id, execution_status, result_summary }",
        "retry_policy": "无重试",
    },
    {
        "event_type": "ROUTE_FAILED",
        "description": "路由计划执行失败",
        "producer": "router_agent",
        "consumers": ["infra"],
        "priority": 1,
        "payload_schema": "{ session_id, plan_id, error_code, error_message }",
        "retry_policy": "最多重试 3 次",
    },

    # ── 用户交互 ──
    {
        "event_type": "USER_QUERY_RECEIVED",
        "description": "用户查询请求已接收",
        "producer": "infra",
        "consumers": ["router_agent"],
        "priority": 1,
        "payload_schema": "ChatMessageRequest",
        "retry_policy": "无重试",
    },
    {
        "event_type": "USER_CONFIRMED",
        "description": "用户确认高危操作",
        "producer": "infra",
        "consumers": ["router_agent"],
        "priority": 1,
        "payload_schema": "{ confirmation_id, session_id, user_id, action_type }",
        "retry_policy": "无重试",
    },
    {
        "event_type": "USER_REJECTED",
        "description": "用户拒绝高危操作",
        "producer": "infra",
        "consumers": ["router_agent"],
        "priority": 1,
        "payload_schema": "{ confirmation_id, session_id, user_id, action_type }",
        "retry_policy": "无重试",
    },

    # ── 整改业务 ──
    {
        "event_type": "RECTIFICATION_CREATED",
        "description": "整改工单已创建",
        "producer": "triage_agent",
        "consumers": ["data_agent", "infra"],
        "priority": 2,
        "payload_schema": "{ task_id, event_id, assignee, deadline }",
        "retry_policy": "无重试",
    },
    {
        "event_type": "RECTIFICATION_UPDATED",
        "description": "整改状态已更新",
        "producer": "triage_agent",
        "consumers": ["infra"],
        "priority": 2,
        "payload_schema": "{ task_id, event_id, old_status, new_status, operator }",
        "retry_policy": "无重试",
    },

    # ── 系统层 ──
    {
        "event_type": "AGENT_HEARTBEAT",
        "description": "Agent 心跳",
        "producer": "router_agent / data_agent / triage_agent",
        "consumers": ["infra"],
        "priority": 5,
        "payload_schema": "{ agent_name, agent_id, status, stats }",
        "retry_policy": "无重试",
    },
    {
        "event_type": "AGENT_ERROR",
        "description": "Agent 异常报告",
        "producer": "router_agent / data_agent / triage_agent",
        "consumers": ["infra"],
        "priority": 1,
        "payload_schema": "{ agent_name, agent_id, error_code, error_message, trace_id }",
        "retry_policy": "无重试",
    },
    {
        "event_type": "SYSTEM_EVENT",
        "description": "系统级事件（配置变更、部署通知等）",
        "producer": "infra",
        "consumers": ["router_agent", "data_agent", "triage_agent"],
        "priority": 3,
        "payload_schema": "{ event_name, payload }",
        "retry_policy": "无重试",
    },
]


# =============================================================================
# 3. 消息总线配置规范
# =============================================================================

MESSAGE_BUS_CONFIG = {
    # Stream 名称
    "stream_topic": "agent_message_bus",

    # 消费者组配置
    "consumer_groups": {
        "triage_agent": {
            "group_name": "triage_consumer_group",
            "consumers": ["triage_001", "triage_002"],
            "description": "监管研判 Agent 消费者组，处理告警相关业务",
        },
        "data_agent": {
            "group_name": "data_consumer_group",
            "consumers": ["data_001", "data_002"],
            "description": "数据分析 Agent 消费者组，处理查询相关业务",
        },
        "router_agent": {
            "group_name": "router_consumer_group",
            "consumers": ["router_001"],
            "description": "路由 Agent 消费者组，处理用户交互相关业务",
        },
        "infra": {
            "group_name": "infra_consumer_group",
            "consumers": ["infra_001"],
            "description": "基建消费者组，处理系统事件、心跳、状态同步",
        },
    },

    # 消费者组读取策略
    "read_strategy": {
        "block_ms": 1000,           # 阻塞等待时间（毫秒）
        "count": 10,                # 每次读取最大消息数
        "claim_idle_ms": 30000,     # 消息空闲超过此时间可被其他消费者认领
    },

    # 消息保留策略
    "retention": {
        "max_len": 100000,          # Stream 最大长度（超出后裁剪旧消息）
        "trim_strategy": "MAXLEN",  # 裁剪策略
    },
}


# =============================================================================
# 4. 错误处理与重试策略
# =============================================================================

"""
错误处理规范:

1. 消息处理失败（回调抛出异常）:
   - 不发送 ACK，消息留在 PEL（Pending Entries List）中
   - 其他消费者可通过 XCLAIM 认领（空闲超过 claim_idle_ms 后）
   - 同一消息最多被处理 3 次，超出后转入死信队列

2. 死信队列:
   - Stream 名称: "agent_message_bus_dlq"
   - 转入时附加字段: __fail_count, __last_error, __failed_agent
   - 运维通过监控 DLQ 长度触发告警

3. 超时处理:
   - 消费者阻塞读取超时（block_ms）后自动重试
   - 消息处理超时（30 秒）视为失败，不 ACK

4. 熔断降级:
   - 参考 BaseAgent 的熔断器实现（FuseState）
   - 连续失败达到阈值后，Agent 自动停止消费新消息
   - 恢复后从 HALF_OPEN 状态重新开始消费
"""

# =============================================================================
# 5. 安全与权限要求
# =============================================================================

"""
安全规范:

1. Redis 认证:
   - 生产环境必须配置 REDIS_PASSWORD
   - Redis 实例应部署在内网，禁止公网暴露

2. 消息加密:
   - 当前阶段：不加密（依赖内网隔离）
   - 未来增强：敏感字段（permission_context 等）使用 AES-256 加密

3. 权限校验:
   - Agent 间通信不校验细粒度权限（信任内网环境）
   - payload 中的 permission_context 由消费方自行校验
   - 禁止在消息总线上透传明文密码、API Key

4. 审计要求:
   - 所有事件发布/消费必须记录 audit log
   - 记录字段: event_type, source_agent, target_agent, event_id, latency_ms
   - 失败事件额外记录: error_code, error_message, retry_count

5. 字段隔离:
   - 禁止在消息总线上传递前端不应见的敏感数据
   - 各 Agent 负责在返回前端前进行数据脱敏
"""


# =============================================================================
# 6. Payload Schema 详细定义
# =============================================================================

# 以下定义补充 schemas.py 中未覆盖的 Payload 结构

ALERT_RECEIVED_PAYLOAD = {
    "description": "网关解析后的告警推送数据",
    "schema": "AlertCoreModel",
    "required_fields": ["id", "camera_id", "message", "violation_type", "level", "confidence", "timestamp"],
}

ALERT_VERIFIED_PAYLOAD = {
    "description": "VLM 二次校验后的违规事件数据",
    "schema": "ViolationEventModel",
    "required_fields": [
        "alert_id", "camera_id", "message", "event_id",
        "is_violation_confirmed", "verification_method", "verified_at",
    ],
}

ROUTE_DISPATCHED_PAYLOAD = {
    "description": "路由分发指令",
    "schema": "Dict",
    "fields": {
        "session_id": "会话ID",
        "plan_id": "执行计划ID",
        "target_agent": "目标Agent名称: router_agent/data_agent/triage_agent",
        "intent_type": "用户意图枚举值",
        "tool_args": "工具调用参数",
        "priority": "优先级 1-5",
    },
}

SQL_BLOCKED_PAYLOAD = {
    "description": "SQL 被 AST 拦截",
    "schema": "Union[ASTSecurityCheckResult, ASTPerformanceCheckResult]",
    "required_fields": ["original_sql", "is_pass", "reason"],
}


# =============================================================================
# 7. 工具函数
# =============================================================================

def get_event_definition(event_type: str) -> Optional[Dict[str, Any]]:
    """按事件类型查询定义"""
    for event in EVENT_TYPE_DEFINITIONS:
        if event["event_type"] == event_type:
            return event
    return None


def list_event_types() -> List[str]:
    """列出所有注册的事件类型"""
    return [e["event_type"] for e in EVENT_TYPE_DEFINITIONS]


def get_consumer_groups() -> Dict[str, Any]:
    """获取消费者组配置"""
    return MESSAGE_BUS_CONFIG["consumer_groups"]


def validate_event_payload(event_type: str, payload: Dict[str, Any]) -> List[str]:
    """校验事件 Payload 的必填字段（轻量级校验，不替代 Pydantic）

    Returns:
        缺失的必填字段列表，空列表表示校验通过
    """
    definition = get_event_definition(event_type)
    if not definition:
        return [f"Unknown event_type: {event_type}"]

    missing = []
    # 根据事件类型检查特定必填字段
    if event_type == "ALERT_RECEIVED":
        for field in ALERT_RECEIVED_PAYLOAD["required_fields"]:
            if field not in payload:
                missing.append(field)
    elif event_type == "ALERT_VERIFIED":
        for field in ALERT_VERIFIED_PAYLOAD["required_fields"]:
            if field not in payload:
                missing.append(field)
    elif event_type == "ROUTE_DISPATCHED":
        for field in ["session_id", "target_agent", "intent_type"]:
            if field not in payload:
                missing.append(field)

    return missing


__all__ = [
    "EVENT_TYPE_DEFINITIONS",
    "MESSAGE_BUS_CONFIG",
    "ALERT_RECEIVED_PAYLOAD",
    "ALERT_VERIFIED_PAYLOAD",
    "ROUTE_DISPATCHED_PAYLOAD",
    "SQL_BLOCKED_PAYLOAD",
    "get_event_definition",
    "list_event_types",
    "get_consumer_groups",
    "validate_event_payload",
]
