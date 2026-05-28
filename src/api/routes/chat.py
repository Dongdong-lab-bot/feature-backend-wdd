"""
前端聊天交互接口契约 (chat.py)

面向前端用户的路由 Agent 交互接口，支持 HTTP 轮询与 WebSocket 实时双模式。
所有外部输入/输出必须符合 src/core/schemas.py 定义。

规范来源: docs/全局schema规范草案.md V1.4
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.core.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConfirmationModel,
    SessionContext,
)


# =============================================================================
# 接口 1: 创建会话
# =============================================================================

async def post_chat_session(
    authorization: str = "",
) -> Dict[str, Any]:
    """创建新的聊天会话

    ---
    **Endpoint**: `POST /api/v1/chat/sessions`

    **认证方式**:
    - Header `Authorization: Bearer <JWT>`
    - JWT 需包含 user_id, role_type, store_ids

    **请求体**: 空（或可选携带初始上下文）

    **响应** (code=0000):
    ```json
    {
      "trace_id": "abc123...",
      "code": "0000",
      "message": "会话创建成功",
      "success": true,
      "response_time": "2026-04-27T15:00:00+08:00",
      "data": {
        "session_id": "SES1745733600123A7F",
        "user_id": "user_001",
        "created_at": "2026-04-27T15:00:00+08:00",
        "expire_time": "2026-04-27T15:30:00+08:00"
      }
    }
    ```

    **会话约束**:
    - session_id 格式: `SES{13位毫秒时间戳}{3位随机大写字母}`
    - 默认过期时间: 30 分钟（无操作后自动过期）
    - 每个用户同时活跃会话数上限: 5 个（超出时返回 1001）
    - **活跃会话判定**: 最后一次消息交互时间距当前 ≤ 30 分钟
    - **超限处理策略**: 创建新会话时，先自动清理最早的非活跃会话；若全部 5 个均为活跃会话，返回 1001 PARAM_ERROR，提示用户关闭历史会话
    - chat_history 最大保留 10 轮

    **错误码**:
    | 错误码 | 错误名称 | 触发场景 | HTTP Status |
    |--------|----------|----------|-------------|
    | 0000 | SUCCESS | 创建成功 | 201 |
    | 1001 | PARAM_ERROR | 活跃会话数超限 | 400 |
    | 3003 | PERMISSION_DENIED | JWT 无效或已过期 | 401 |
    | 5001 | AGENT_INIT_FAILED | 路由 Agent 初始化失败 | 503 |

    **审计要求**:
    - 记录 audit log（event_type=USER_LOGIN）
    """
    raise NotImplementedError("接口契约，待实现")


# =============================================================================
# 接口 2: HTTP 发送消息
# =============================================================================

async def post_chat_message(
    request: ChatMessageRequest,
    authorization: str = "",
) -> ChatMessageResponse:
    """通过 HTTP 发送聊天消息并同步获取响应

    ---
    **Endpoint**: `POST /api/v1/chat/messages`

    **认证方式**:
    - Header `Authorization: Bearer <JWT>`

    **请求体** (`ChatMessageRequest`):
    ```json
    {
      "trace_id": "auto-generated",
      "user_id": "user_001",
      "request_time": "2026-04-27T15:00:00+08:00",
      "session_id": "SES1745733600123A7F",
      "message_text": "查询今天南山店的告警",
      "input_type": "text",
      "attachments": null,
      "confirmation_id": null
    }
    ```

    **处理流程**:
    1. 校验 JWT 与 session_id 归属（session.user_id 必须等于 JWT user_id）
    2. 更新会话上下文（updated_at = now, expire_time 延长 30 分钟）
    3. 路由 Agent 进行意图识别（IntentRecognitionResult）
    4. 若意图置信度不足 → 返回 clarification 响应
    5. 若需要二次确认（高危操作）→ 生成 ConfirmationModel，返回 confirmation_preview
    6. 路由到目标 Agent（data_agent / triage_agent）
    7. 聚合结果，返回 ChatMessageResponse
    8. 更新 session.chat_history

    **响应** (`ChatMessageResponse`):
    根据 `response_type` 区分：
    - `answer`: 直接回答，answer_payload 为文本，structured_summary 可能含图表数据
    - `clarification`: 需要澄清，clarification_content 为追问话术
    - `confirmation_preview`: 高危操作预览，pending_confirmation 含操作详情
    - `refusal`: 拒绝处理（越权/安全拦截）
    - `error`: 系统错误
    - `guidance`: 引导用户进行下一步操作

    **错误码**:
    | 错误码 | 错误名称 | 触发场景 | HTTP Status |
    |--------|----------|----------|-------------|
    | 0000 | SUCCESS | 处理成功 | 200 |
    | 1001 | PARAM_ERROR | session_id 不存在 / message_text 为空 / input_type 非法 | 400 |
    | 3003 | PERMISSION_DENIED | JWT 无效 / 非会话所有者 | 401/403 |
    | 5002 | AGENT_HANDLE_FAILED | 路由 Agent 处理异常 | 500 |
    | 6001 | INTENT_RECOGNITION_FAILED | 意图识别置信度不足 | 422 |
    | 6002 | ROUTE_DISPATCH_FAILED | 目标 Agent 不可用 | 503 |
    | 6003 | CONFIRMATION_EXPIRED | 二次确认单已过期 | 410 |
    | 2001 | LLM_CALL_FAILED | 大模型调用失败（3次重试后） | 503 |
    | 2003 | LLM_FUSE_TRIGGERED | 大模型熔断已触发 | 503 |

    **超时设置**:
    - 整体接口超时: 30 秒（含意图识别 + 路由 + 目标 Agent 处理）
    - 超过 30 秒返回 5002，message="请求处理超时，请稍后重试"

    **审计要求**:
    - 记录 audit log（event_type=USER_QUERY），含 message_text、intent_type、latency_ms
    """
    raise NotImplementedError("接口契约，待实现")


# =============================================================================
# 接口 3: 获取会话信息
# =============================================================================

async def get_chat_session(
    session_id: str,
    authorization: str = "",
) -> Dict[str, Any]:
    """获取会话基本信息与状态

    ---
    **Endpoint**: `GET /api/v1/chat/sessions/{session_id}`

    **认证方式**:
    - Header `Authorization: Bearer <JWT>`

    **路径参数**:
    | 字段名     | 类型   | 必填 | 说明       |
    |------------|--------|------|------------|
    | session_id | string | 是   | 会话 ID    |

    **权限校验**:
    - 仅会话所有者（session.user_id == JWT.user_id）可访问
    - ENTERPRISE_ADMIN 可查看全部会话（用于运维）

    **响应**:
    返回 `SessionContext` 的脱敏版本（不含敏感字段）。

    **错误码**:
    | 错误码 | 错误名称 | 触发场景 | HTTP Status |
    |--------|----------|----------|-------------|
    | 0000 | SUCCESS | 查询成功 | 200 |
    | 1001 | PARAM_ERROR | session_id 格式非法 | 400 |
    | 3003 | PERMISSION_DENIED | 非会话所有者 | 403 |
    | 4003 | DB_RESULT_EMPTY | session_id 不存在 | 404 |
    """
    raise NotImplementedError("接口契约，待实现")


# =============================================================================
# 接口 4: 获取对话历史
# =============================================================================

async def get_chat_history(
    session_id: str,
    authorization: str = "",
    page_num: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """分页获取会话的对话历史

    ---
    **Endpoint**: `GET /api/v1/chat/sessions/{session_id}/history`

    **认证方式**:
    - Header `Authorization: Bearer <JWT>`

    **路径参数**:
    | 字段名     | 类型   | 必填 | 说明       |
    |------------|--------|------|------------|
    | session_id | string | 是   | 会话 ID    |

    **查询参数**:
    | 字段名    | 类型    | 默认值 | 说明         |
    |-----------|---------|--------|--------------|
    | page_num  | integer | 1      | 页码         |
    | page_size | integer | 20     | 每页条数     |

    **响应**:
    ```json
    {
      "trace_id": "...",
      "code": "0000",
      "message": "查询成功",
      "success": true,
      "response_time": "...",
      "data": {
        "total": 15,
        "page_num": 1,
        "page_size": 20,
        "total_pages": 1,
        "items": [
          {
            "role": "user",
            "message_text": "查询今天告警",
            "timestamp": "2026-04-27T15:00:00+08:00",
            "intent_type": "query_summary"
          },
          {
            "role": "assistant",
            "answer_payload": "今天共有 5 条告警...",
            "response_type": "answer",
            "timestamp": "2026-04-27T15:00:03+08:00"
          }
        ]
      }
    }
    ```

    **错误码**: 同接口 3
    """
    raise NotImplementedError("接口契约，待实现")


# =============================================================================
# 接口 5: WebSocket 实时对话
# =============================================================================

async def ws_chat(
    session_id: str,
) -> None:
    """WebSocket 实时对话通道

    ---
    **Endpoint**: `WS /ws/v1/chat/{session_id}`

    **认证方式**:
    - 连接建立后，Client 必须在第一条消息中发送认证包完成 JWT 校验
    - 认证包格式：`{"auth": "<JWT>"}`
    - 服务端收到认证包后校验 JWT 有效性与 session 归属
    - 认证失败时立即关闭连接（code=1008, reason="Unauthorized"）
    - **禁止在 URL Query Param、Path、Header 中传递 JWT**，防止 Token 被网关/代理日志明文记录

    **路径参数**:
    | 字段名     | 类型   | 必填 | 说明       |
    |------------|--------|------|------------|
    | session_id | string | 是   | 会话 ID    |

    **消息格式**:
    所有消息均为 JSON 字符串。

    **Client → Server**:
    ```json
    {
      "message_text": "查询今天南山店的告警",
      "input_type": "text",
      "attachments": null,
      "confirmation_id": null
    }
    ```

    **Server → Client**:
    ```json
    {
      "session_id": "SES1745733600123A7F",
      "response_type": "answer",
      "answer_payload": "今天南山店共有 3 条告警...",
      "structured_summary": { "total": 3, "items": [...] },
      "guidance_type": "none",
      "suggested_actions": [
        { "label": "查看详情", "action": "query_detail" }
      ],
      "pending_confirmation": null
    }
    ```

    **连接管理**:
    - 心跳: Server 每 30 秒发送一次 ping，Client 需在 10 秒内回复 pong
    - 连续 3 次心跳未回复 pong → Server 断开连接（避免网络抖动导致频繁断连）
    - 同一 session 支持多端同时连接（多端同步推送）
    - 会话过期（30 分钟无操作）→ Server 发送过期通知后断开连接

    **Client → Server 认证消息（连接后第一条）**:
    ```json
    {"auth": "eyJhbGciOiJIUzI1NiIs..."}
    ```
    服务端校验通过后回复 `{"type": "auth_ok"}`，此后进入正常消息交互。

    **错误消息** (Server → Client):
    ```json
    {
      "response_type": "error",
      "answer_payload": "会话已过期，请重新创建会话",
      "code": "6003"
    }
    ```

    **权限校验**:
    - 同接口 2，仅会话所有者可连接
    - 非所有者尝试连接 → 立即断开（code=1008, reason="Forbidden"）

    **审计要求**:
    - 连接建立/断开记录 audit log
    - 每条消息处理记录 audit log（event_type=USER_QUERY）
    """
    raise NotImplementedError("接口契约，待实现")


# =============================================================================
# 接口 6: 确认高危操作
# =============================================================================

async def post_confirmation_confirm(
    confirmation_id: str,
    authorization: str = "",
) -> ChatMessageResponse:
    """用户确认高危操作

    ---
    **Endpoint**: `POST /api/v1/chat/confirmations/{confirmation_id}/confirm`

    **认证方式**:
    - Header `Authorization: Bearer <JWT>`

    **路径参数**:
    | 字段名         | 类型   | 必填 | 说明         |
    |----------------|--------|------|--------------|
    | confirmation_id| string | 是   | 确认单 ID    |

    **处理流程**:
    1. 校验确认单是否存在且未过期
    2. 校验用户是否为确认单所有者
    3. 执行确认单中的 action_type（export_report / send_notice / create_task）
    4. 更新确认单状态为 confirmed
    5. 返回执行结果

    **响应**: `ChatMessageResponse` (response_type="answer" 或 "error")

    **错误码**:
    | 错误码 | 错误名称 | 触发场景 | HTTP Status |
    |--------|----------|----------|-------------|
    | 0000 | SUCCESS | 确认成功并执行 | 200 |
    | 1001 | PARAM_ERROR | confirmation_id 格式非法 | 400 |
    | 3003 | PERMISSION_DENIED | 非确认单所有者 | 403 |
    | 6003 | CONFIRMATION_EXPIRED | 确认单已过期 | 410 |
    | 4003 | DB_RESULT_EMPTY | confirmation_id 不存在 | 404 |
    | 5002 | AGENT_HANDLE_FAILED | 操作执行失败 | 500 |

    **审计要求**:
    - 记录 audit log（event_type=USER_ACTION_CONFIRM）
    """
    raise NotImplementedError("接口契约，待实现")


# =============================================================================
# 接口 7: 拒绝高危操作
# =============================================================================

async def post_confirmation_reject(
    confirmation_id: str,
    authorization: str = "",
) -> ChatMessageResponse:
    """用户拒绝高危操作

    ---
    **Endpoint**: `POST /api/v1/chat/confirmations/{confirmation_id}/reject`

    **认证方式**:
    - Header `Authorization: Bearer <JWT>`

    **路径参数**: 同接口 6

    **处理流程**:
    1. 校验确认单是否存在且未过期
    2. 校验用户是否为确认单所有者
    3. 更新确认单状态为 rejected
    4. 返回拒绝确认

    **响应**: `ChatMessageResponse` (response_type="answer")

    **错误码**: 同接口 6

    **审计要求**:
    - 记录 audit log（event_type=USER_ACTION_REJECT）
    """
    raise NotImplementedError("接口契约，待实现")


# =============================================================================
# 接口 8: 删除会话
# =============================================================================

async def delete_chat_session(
    session_id: str,
    authorization: str = "",
) -> Dict[str, Any]:
    """删除会话（软删除）

    ---
    **Endpoint**: `DELETE /api/v1/chat/sessions/{session_id}`

    **认证方式**:
    - Header `Authorization: Bearer <JWT>`

    **路径参数**:
    | 字段名     | 类型   | 必填 | 说明       |
    |------------|--------|------|------------|
    | session_id | string | 是   | 会话 ID    |

    **权限校验**:
    - 仅会话所有者或 ENTERPRISE_ADMIN 可删除

    **响应**:
    ```json
    {
      "trace_id": "...",
      "code": "0000",
      "message": "会话已删除",
      "success": true,
      "response_time": "...",
      "data": null
    }
    ```

    **错误码**:
    | 错误码 | 错误名称 | 触发场景 | HTTP Status |
    |--------|----------|----------|-------------|
    | 0000 | SUCCESS | 删除成功 | 200 |
    | 3003 | PERMISSION_DENIED | 无权删除 | 403 |
    | 4003 | DB_RESULT_EMPTY | session_id 不存在 | 404 |
    """
    raise NotImplementedError("接口契约，待实现")


__all__ = [
    "post_chat_session",
    "post_chat_message",
    "get_chat_session",
    "get_chat_history",
    "ws_chat",
    "post_confirmation_confirm",
    "post_confirmation_reject",
    "delete_chat_session",
]
