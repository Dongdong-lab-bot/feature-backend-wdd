"""聊天路由 API：JWT 认证 + RouterService + 会话管理。"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.agents.router_agent.auth import parse_jwt_user
from src.agents.router_agent.context_manager import context_manager_singleton
from src.agents.router_agent.router_service import RouterService
from src.core.exceptions import AgentHandleFailedError, ProjectBaseException
from src.core.logger import TraceContext, log
from src.core.schemas import (
    ActionTypeEnum,
    ChatMessageResponse,
    ConfirmationModel,
    UserIntentEnum,
    beijing_now,
    generate_id,
)


_TRACE_ID_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")
_MAX_MESSAGE_LENGTH = 2000
_GUIDANCE_COOLDOWN_SECONDS = 300

_SESSION_MANAGER = context_manager_singleton
_ROUTER_SERVICE = RouterService.get_instance()


class ChatRouterPayload(BaseModel):
    """chat_router 内部入参模型（后续直接对接 ChatMessageRequest + Authorization）。"""

    session_id: str = Field(min_length=1, description="会话ID")
    message: str = Field(min_length=1, max_length=_MAX_MESSAGE_LENGTH, description="用户消息内容")
    authorization: str = Field(min_length=8, description="Bearer JWT")
    trace_id: str | None = Field(default=None, description="追踪ID")
    request_id: str | None = Field(default=None, description="请求ID")
    input_type: str = Field(default="text", description="输入类型：text/confirmation")
    confirmation_id: str | None = Field(default=None, description="确认单ID")
    confirmation_action: str | None = Field(default=None, description="确认动作：confirm/reject")

    @field_validator("trace_id")
    @classmethod
    def _validate_trace_id(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        if not _TRACE_ID_PATTERN.match(v):
            raise ValueError("trace_id 必须为 32 位十六进制字符串")
        return v


async def handle_chat_router(request: ChatRouterPayload) -> dict[str, Any]:
    """路由入口处理函数。"""
    try:
        trace_id = (request.trace_id or "").strip()
        if trace_id:
            TraceContext.set_trace_id(trace_id)
        else:
            trace_id = TraceContext.get_trace_id()

        user = parse_jwt_user(request.authorization)
        await _SESSION_MANAGER.cleanup_expired_confirmations(session_id=request.session_id)

        if request.confirmation_id:
            return await _handle_confirmation_message(
                request=request,
                user_id=user.user_id,
                user_role=user.user_role,
                trace_id=trace_id,
            )

        session_state = await _SESSION_MANAGER.upsert_user_message(
            session_id=request.session_id,
            user_id=user.user_id,
            user_role=user.user_role,
            user_message=request.message,
        )

        route_result = await _ROUTER_SERVICE.route(
            message=request.message,
            user_role=user.user_role,
            chat_history=[msg.model_dump(mode="json") for msg in session_state.chat_history],
        )

        response_type = "answer"
        code = "0000"
        success = True
        answer_payload = _default_reply_by_intent(route_result.intent_type)

        if route_result.is_out_of_domain or route_result.intent_type == UserIntentEnum.OUT_OF_DOMAIN:
            response_type = "refusal"
            code = "6001"
            success = False
            answer_payload = route_result.clarification_content or _default_reply_by_intent(UserIntentEnum.OUT_OF_DOMAIN)
        elif route_result.missing_slots:
            response_type = "clarification"
            code = "6001"
            success = False
            answer_payload = _clarification_by_missing_slots(route_result.missing_slots)
        elif _ROUTER_SERVICE.is_low_confidence(route_result):
            response_type = "clarification"
            code = "6001"
            success = False
            answer_payload = route_result.clarification_content or "请补充你的具体需求，我再继续处理。"

        pending_confirmation: ConfirmationModel | None = None
        if success and _ROUTER_SERVICE.needs_confirmation(route_result):
            response_type = "confirmation_preview"
            answer_payload = "该操作涉及高风险写入，请先确认后我再继续执行。"
            pending_confirmation = ConfirmationModel(
                confirmation_id=generate_id("CNF"),
                session_id=request.session_id,
                user_id=user.user_id,
                action_type=_intent_to_action(route_result.intent_type),
                action_preview=_confirmation_preview(route_result.intent_type),
                action_params=route_result.tool_args or {},
            )
            await _SESSION_MANAGER.save_confirmation(pending_confirmation)

        suggested_actions_base = _suggested_actions(route_result.intent_type, response_type=response_type)
        suggested_actions, guidance_meta = _apply_guidance_cooldown(
            session_state=session_state,
            response_type=response_type,
            suggested_actions=suggested_actions_base,
        )

        await _SESSION_MANAGER.update_route_context(
            session_id=request.session_id,
            intent_type=route_result.intent_type,
            pending_confirmation_id=(pending_confirmation.confirmation_id if pending_confirmation else None),
            result_snapshot={
                "target_agent": route_result.target_agent,
                "target_tool": route_result.target_tool,
                "tool_args": route_result.tool_args,
                "response_type": response_type,
                "guidance_signature": guidance_meta["guidance_signature"],
                "guidance_at": guidance_meta["guidance_at"],
                "guidance_suppressed": guidance_meta["guidance_suppressed"],
            },
        )

        await _SESSION_MANAGER.append_assistant_message(
            session_id=request.session_id,
            reply=answer_payload,
            intent_type=route_result.intent_type,
        )

        response = ChatMessageResponse(
            code=code,
            message="ok" if success else "需要澄清",
            success=success,
            trace_id=trace_id,
            response_time=beijing_now(),
            data={"request_id": request.request_id, "user_id": user.user_id},
            session_id=request.session_id,
            response_type=response_type,
            answer_payload=answer_payload,
            structured_summary=_build_route_summary(
                session_state=session_state,
                route_result=route_result,
                response_type=response_type,
            ),
            guidance_type="followup_query" if suggested_actions and response_type in {"clarification", "refusal"} else "none",
            suggested_actions=suggested_actions,
            pending_confirmation=pending_confirmation,
        )
        return response.model_dump(mode="json")
    except asyncio.CancelledError:
        raise
    except ProjectBaseException as exc:
        return exc.to_dict()
    except Exception as exc:  # pragma: no cover
        log.error(f"chat_router 未预期异常: {exc}")
        return AgentHandleFailedError(
            message="路由处理失败",
            detail={"reason": "内部处理异常，请稍后重试"},
        ).to_dict()
    finally:
        TraceContext.clear_trace_id()


def _intent_to_action(intent: UserIntentEnum) -> ActionTypeEnum:
    if intent == UserIntentEnum.CREATE_TASK:
        return ActionTypeEnum.CREATE_TASK
    if intent == UserIntentEnum.EXPORT_REPORT:
        return ActionTypeEnum.EXPORT_REPORT
    return ActionTypeEnum.SEND_NOTICE


async def _handle_confirmation_message(
    *,
    request: ChatRouterPayload,
    user_id: str,
    user_role: Any,
    trace_id: str,
) -> dict[str, Any]:
    action = _infer_confirmation_action(request)
    confirmation = await _SESSION_MANAGER.resolve_confirmation(
        confirmation_id=request.confirmation_id or "",
        user_id=user_id,
        session_id=request.session_id,
        action=action,
    )

    await _SESSION_MANAGER.upsert_user_message(
        session_id=request.session_id,
        user_id=user_id,
        user_role=user_role,
        user_message=request.message,
    )

    if confirmation.confirmation_status == "confirmed":
        answer_payload = "已记录确认。高风险动作将由下游 Agent 按确认单参数执行。"
    else:
        answer_payload = "已取消本次高风险操作。"

    await _SESSION_MANAGER.update_route_context(
        session_id=request.session_id,
        intent_type=UserIntentEnum.CONFIRM_ACTION if action == "confirm" else UserIntentEnum.REJECT_ACTION,
        pending_confirmation_id=None,
        result_snapshot={
            "confirmation_id": confirmation.confirmation_id,
            "confirmation_status": confirmation.confirmation_status,
            "action_type": confirmation.action_type.value,
        },
    )
    await _SESSION_MANAGER.append_assistant_message(
        session_id=request.session_id,
        reply=answer_payload,
        intent_type=UserIntentEnum.CONFIRM_ACTION if action == "confirm" else UserIntentEnum.REJECT_ACTION,
    )

    response = ChatMessageResponse(
        code="0000",
        message="ok",
        success=True,
        trace_id=trace_id,
        response_time=beijing_now(),
        data={"request_id": request.request_id, "user_id": user_id},
        session_id=request.session_id,
        response_type="answer",
        answer_payload=answer_payload,
        structured_summary={
            "confirmation_id": confirmation.confirmation_id,
            "confirmation_status": confirmation.confirmation_status,
            "action_type": confirmation.action_type.value,
            "execution_status": "waiting_downstream" if action == "confirm" else "cancelled",
            "action_params": confirmation.action_params,
        },
        guidance_type="none",
        suggested_actions=[],
        pending_confirmation=None,
    )
    return response.model_dump(mode="json")


def _infer_confirmation_action(request: ChatRouterPayload) -> str:
    if request.confirmation_action in {"confirm", "reject"}:
        return request.confirmation_action
    text = request.message.strip().lower()
    if text in {"reject", "cancel", "取消", "拒绝", "不确认", "否"}:
        return "reject"
    return "confirm"


def _confirmation_preview(intent: UserIntentEnum) -> str:
    if intent == UserIntentEnum.EXPORT_REPORT:
        return "请确认是否导出当前报表。"
    if intent == UserIntentEnum.CREATE_TASK:
        return "请确认是否创建整改工单。"
    return "请确认是否执行下发/整改类操作。"


def _clarification_by_missing_slots(missing_slots: list[str]) -> str:
    if "alert_id_or_event_id" in missing_slots:
        return "请补充要处理的告警 ID 或事件 ID，我再生成确认预览。"
    return "请补充关键信息后我再继续处理。"


def _default_reply_by_intent(intent: UserIntentEnum) -> str:
    if intent in {
        UserIntentEnum.QUERY_SUMMARY,
        UserIntentEnum.QUERY_DETAIL,
        UserIntentEnum.QUERY_TREND,
        UserIntentEnum.QUERY_RANKING,
        UserIntentEnum.QUERY_RECTIFICATION,
    }:
        return "收到，我正在帮你查询对应数据。"
    if intent in {UserIntentEnum.SEND_NOTICE, UserIntentEnum.CREATE_TASK, UserIntentEnum.EXPORT_REPORT}:
        return "收到，我先生成操作预览供你确认。"
    if intent == UserIntentEnum.OUT_OF_DOMAIN:
        return "这个问题暂不在食安业务处理范围内，我可以继续帮你处理告警、报表和整改。"
    return "我已收到你的请求。"


def _build_route_summary(*, session_state: Any, route_result: Any, response_type: str) -> dict[str, Any]:
    slots = route_result.slots or {}
    tool_args = route_result.tool_args or {}
    return {
        "session_history_size": len(session_state.chat_history),
        "session_expire_time": session_state.expire_time.isoformat(),
        "intent_type": route_result.intent_type.value,
        "intent_confidence": route_result.intent_confidence,
        "target_agent": route_result.target_agent,
        "target_tool": route_result.target_tool,
        "tool_args": tool_args,
        "slots": slots,
        "missing_slots": route_result.missing_slots,
        "dispatch_status": _dispatch_status(response_type),
        "entity_boundary": slots.get("entity_boundary", {}),
    }


def _apply_guidance_cooldown(
    *,
    session_state: Any,
    response_type: str,
    suggested_actions: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if not suggested_actions:
        return suggested_actions, {
            "guidance_signature": None,
            "guidance_at": None,
            "guidance_suppressed": False,
        }

    now = beijing_now()
    signature = _guidance_signature(suggested_actions)
    guidance_meta = {
        "guidance_signature": signature,
        "guidance_at": now.isoformat(),
        "guidance_suppressed": False,
    }

    if response_type not in {"clarification", "refusal", "guidance"}:
        return suggested_actions, guidance_meta

    snapshot = session_state.last_result_snapshot or {}
    last_signature = str(snapshot.get("guidance_signature") or "")
    last_at = _parse_iso_datetime(snapshot.get("guidance_at"))
    if signature != last_signature or last_at is None:
        return suggested_actions, guidance_meta

    if now - last_at < timedelta(seconds=_GUIDANCE_COOLDOWN_SECONDS):
        guidance_meta["guidance_suppressed"] = True
        guidance_meta["guidance_at"] = last_at.isoformat()
        return [], guidance_meta

    return suggested_actions, guidance_meta


def _guidance_signature(suggested_actions: list[dict[str, str]]) -> str:
    normalized = [f"{item.get('action', '')}:{item.get('label', '')}" for item in suggested_actions]
    normalized.sort()
    return "|".join(normalized)


def _parse_iso_datetime(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        value = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return value if value.tzinfo is not None else None


def _dispatch_status(response_type: str) -> str:
    if response_type == "confirmation_preview":
        return "waiting_confirmation"
    if response_type == "clarification":
        return "waiting_clarification"
    if response_type == "refusal":
        return "refused"
    return "planned"


def _suggested_actions(intent: UserIntentEnum, *, response_type: str = "answer") -> list[dict[str, str]]:
    if intent == UserIntentEnum.NEED_CLARIFICATION:
        return [
            {"label": "查看今日告警", "action": "query_summary"},
            {"label": "发起整改通知", "action": "send_notice"},
        ]
    if intent == UserIntentEnum.OUT_OF_DOMAIN:
        return [
            {"label": "查看今日告警", "action": "query_summary"},
            {"label": "查询整改进度", "action": "query_rectification"},
        ]
    if response_type == "clarification":
        return []
    if intent in {UserIntentEnum.SEND_NOTICE, UserIntentEnum.CREATE_TASK, UserIntentEnum.EXPORT_REPORT}:
        return [{"label": "确认执行", "action": "confirm_action"}, {"label": "取消", "action": "reject_action"}]
    return []


async def _session_snapshot() -> dict[str, Any]:
    """测试与联调用：返回会话快照。"""
    return await _SESSION_MANAGER.snapshot()


__all__ = ["handle_chat_router", "_session_snapshot", "ChatRouterPayload"]
