from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.llm_client import AsyncLLMClient
from src.core.logger import log
from src.core.schemas import IntentRecognitionResult, QuerySceneEnum, UserIntentEnum, UserRoleEnum


class TargetAgent(str, Enum):
    """兼容早期路由测试与文档口径的目标 Agent 枚举。"""

    DATA_AGENT = "data_agent"
    TRIAGE_AGENT = "triage_agent"
    ROUTER_AGENT = "router_agent"


class IntentType(str, Enum):
    """兼容早期 Function Calling 产物的意图枚举。"""

    GREETING = "greeting"
    QUERY_VIOLATION = "query_violation"
    QUERY_REPORT = "query_report"
    DISPATCH_ACTION = "dispatch_action"
    COMPLIANCE_CONSULT = "compliance_consult"
    UNKNOWN = "unknown"


class RouterIntentRecognitionResult(IntentRecognitionResult):
    """路由结果模型。

    主字段遵循全局 `IntentRecognitionResult`；只读兼容属性用于承接早期测试与旧文档。
    """

    @property
    def intent(self) -> IntentType:
        if self.intent_type in {
            UserIntentEnum.QUERY_DETAIL,
            UserIntentEnum.QUERY_RECTIFICATION,
        }:
            return IntentType.QUERY_VIOLATION
        if self.intent_type in {
            UserIntentEnum.QUERY_SUMMARY,
            UserIntentEnum.QUERY_TREND,
            UserIntentEnum.QUERY_RANKING,
        }:
            return IntentType.QUERY_REPORT
        if self.intent_type in {
            UserIntentEnum.SEND_NOTICE,
            UserIntentEnum.CREATE_TASK,
            UserIntentEnum.EXPORT_REPORT,
        }:
            return IntentType.DISPATCH_ACTION
        return IntentType.UNKNOWN

    @property
    def confidence(self) -> float:
        return self.intent_confidence

    @property
    def need_confirmation(self) -> bool:
        return bool((self.tool_args or {}).get("requires_confirmation")) or self.intent_type in {
            UserIntentEnum.SEND_NOTICE,
            UserIntentEnum.CREATE_TASK,
            UserIntentEnum.EXPORT_REPORT,
        }


class RouterService:
    """基于 LLM Function Calling + 关键词兜底的路由服务。"""

    LOW_CONFIDENCE_THRESHOLD = 0.7

    _INSTANCE: "RouterService | None" = None

    _GREETING_KEYWORDS = ["你好", "您好", "hello", "hi", "在吗"]
    _VIOLATION_KEYWORDS = ["违规", "告警", "抓拍", "未戴口罩", "风险"]
    _TREND_KEYWORDS = ["趋势", "走势", "环比", "同比"]
    _RANKING_KEYWORDS = ["排名", "排行", "top", "最高", "最多"]
    _REPORT_KEYWORDS = ["报表", "统计", "汇总", "分析"]
    _RECTIFICATION_QUERY_KEYWORDS = ["整改状态", "整改进度", "整改情况", "是否整改", "整改完成", "逾期整改"]
    _CREATE_TASK_KEYWORDS = ["创建整改", "创建工单", "生成工单", "新建工单", "工单"]
    _DISPATCH_KEYWORDS = ["下发", "通知", "催办", "提醒", "发起整改"]
    _EXPORT_KEYWORDS = ["导出", "下载", "生成报表"]
    _COMPLIANCE_KEYWORDS = ["法规", "条例", "规范", "合规", "依据"]
    _OUT_OF_DOMAIN_KEYWORDS = ["天气", "股票", "彩票", "电影", "旅游", "代码", "论文"]

    _ALERT_ID_PATTERN = re.compile(r"\bALT[0-9A-Z]{8,}\b", re.IGNORECASE)
    _EVENT_ID_PATTERN = re.compile(r"\bEVE[0-9A-Z]{8,}\b", re.IGNORECASE)
    _TASK_ID_PATTERN = re.compile(r"\b(?:TSK|TASK|RECT)[0-9A-Z_-]{4,}\b", re.IGNORECASE)

    _SYSTEM_PROMPT_FILE = Path(__file__).resolve().parents[2] / "prompts" / "router_intent_system_prompt.txt"
    _FUNCTION_NAME = "route_intent"

    _INTENT_TOOL_SCHEMA = {
        "type": "function",
        "function": {
            "name": _FUNCTION_NAME,
            "description": "识别用户意图并给出路由决策",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent_type": {"type": "string", "enum": [i.value for i in UserIntentEnum]},
                    "intent_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "slots": {"type": "object"},
                    "missing_slots": {"type": "array", "items": {"type": "string"}},
                    "target_agent": {"type": "string"},
                    "target_tool": {"type": ["string", "null"]},
                    "tool_args": {"type": ["object", "null"]},
                    "need_clarification": {"type": "boolean"},
                    "clarification_content": {"type": ["string", "null"]},
                    "is_out_of_domain": {"type": "boolean"},
                },
                "required": [
                    "intent_type",
                    "intent_confidence",
                    "slots",
                    "missing_slots",
                    "target_agent",
                    "target_tool",
                    "tool_args",
                    "need_clarification",
                    "clarification_content",
                    "is_out_of_domain",
                ],
                "additionalProperties": False,
            },
        },
    }

    def __init__(self, llm_client: AsyncLLMClient | None = None):
        if llm_client is not None:
            self._llm_client = llm_client
        else:
            try:
                self._llm_client = AsyncLLMClient()
            except Exception as exc:
                log.warning(f"AsyncLLMClient 初始化失败，自动降级关键词路由: {exc}")
                self._llm_client = None
        self._system_prompt = self._load_system_prompt()

    @classmethod
    def get_instance(cls) -> "RouterService":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    async def close(self) -> None:
        if self._llm_client is not None:
            await self._llm_client.close()

    def detect_intent(self, message: str) -> UserIntentEnum:
        text = (message or "").strip().lower()
        if not text:
            return UserIntentEnum.NEED_CLARIFICATION

        if self._contains_any(text, self._CREATE_TASK_KEYWORDS):
            return UserIntentEnum.CREATE_TASK
        if self._contains_any(text, self._DISPATCH_KEYWORDS):
            return UserIntentEnum.SEND_NOTICE
        if self._contains_any(text, self._EXPORT_KEYWORDS):
            return UserIntentEnum.EXPORT_REPORT
        if self._contains_any(text, self._RECTIFICATION_QUERY_KEYWORDS):
            return UserIntentEnum.QUERY_RECTIFICATION
        if self._contains_any(text, self._TREND_KEYWORDS):
            return UserIntentEnum.QUERY_TREND
        if self._contains_any(text, self._RANKING_KEYWORDS):
            return UserIntentEnum.QUERY_RANKING
        if self._contains_any(text, self._REPORT_KEYWORDS):
            return UserIntentEnum.QUERY_SUMMARY
        if self._contains_any(text, self._VIOLATION_KEYWORDS):
            return UserIntentEnum.QUERY_DETAIL
        if self._contains_any(text, self._COMPLIANCE_KEYWORDS):
            return UserIntentEnum.QUERY_DETAIL
        if self._contains_any(text, self._GREETING_KEYWORDS):
            return UserIntentEnum.NEED_CLARIFICATION
        if self._contains_any(text, self._OUT_OF_DOMAIN_KEYWORDS):
            return UserIntentEnum.OUT_OF_DOMAIN
        return UserIntentEnum.NEED_CLARIFICATION

    async def route(
        self,
        message: str,
        user_role: UserRoleEnum,
        chat_history: list[dict[str, Any]] | None = None,
    ) -> IntentRecognitionResult:
        llm_result = await self._route_by_llm(
            message=message,
            user_role=user_role,
            chat_history=chat_history or [],
        )
        if llm_result is not None:
            return llm_result
        return self._route_by_keywords(message)

    async def _route_by_llm(
        self,
        *,
        message: str,
        user_role: UserRoleEnum,
        chat_history: list[dict[str, Any]],
    ) -> IntentRecognitionResult | None:
        if not message.strip() or not self._system_prompt:
            return None
        if self._llm_client is None:
            return None

        user_prompt = (
            f"用户角色: {user_role.value}\n"
            f"用户消息: {message}\n"
            f"最近对话: {json.dumps(chat_history[-4:], ensure_ascii=False)}\n"
            "请调用 route_intent 并输出结构化路由。"
        )

        try:
            response = await self._llm_client.chat(
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                trace_id="router-intent",
                temperature=0.0,
                provider_id="default",
                return_response_object=True,
                tools=[self._INTENT_TOOL_SCHEMA],
                tool_choice={"type": "function", "function": {"name": self._FUNCTION_NAME}},
            )
            return self._parse_route_from_response(response=response, user_query=message)
        except Exception as exc:  # pragma: no cover
            log.warning(f"router llm route failed, fallback to keywords: {exc}")
            return None

    def _route_by_keywords(self, message: str) -> RouterIntentRecognitionResult:
        intent = self.detect_intent(message)
        slots = self._extract_entity_slots(message)

        if intent in {
            UserIntentEnum.QUERY_SUMMARY,
            UserIntentEnum.QUERY_DETAIL,
            UserIntentEnum.QUERY_TREND,
            UserIntentEnum.QUERY_RANKING,
            UserIntentEnum.QUERY_RECTIFICATION,
        }:
            return RouterIntentRecognitionResult(
                user_query=message,
                intent_type=intent,
                intent_confidence=0.86,
                slots=slots,
                target_agent="data_agent",
                target_tool="query_food_safety_data",
                tool_args=self._build_tool_args(intent=intent, slots=slots, requires_confirmation=False),
            )

        if intent in {UserIntentEnum.SEND_NOTICE, UserIntentEnum.CREATE_TASK, UserIntentEnum.EXPORT_REPORT}:
            return RouterIntentRecognitionResult(
                user_query=message,
                intent_type=intent,
                intent_confidence=0.84,
                slots=slots,
                target_agent="triage_agent",
                target_tool="preview_dispatch_action",
                missing_slots=self._missing_slots_for_write(intent=intent, slots=slots),
                tool_args=self._build_tool_args(intent=intent, slots=slots, requires_confirmation=True),
            )

        if intent == UserIntentEnum.OUT_OF_DOMAIN:
            return RouterIntentRecognitionResult(
                user_query=message,
                intent_type=UserIntentEnum.OUT_OF_DOMAIN,
                intent_confidence=0.88,
                slots=slots,
                target_agent="router_agent",
                target_tool="refuse_out_of_domain",
                tool_args={"requires_confirmation": False},
                need_clarification=False,
                clarification_content=None,
                is_out_of_domain=True,
            )

        return RouterIntentRecognitionResult(
            user_query=message,
            intent_type=UserIntentEnum.NEED_CLARIFICATION,
            intent_confidence=0.56,
            slots=slots,
            target_agent="router_agent",
            target_tool="request_clarification",
            tool_args={"clarification_slots": ["task_type"]},
            need_clarification=True,
            clarification_content="我可以帮你查告警、报表，或发起整改通知。你现在想做哪一项？",
            is_out_of_domain=False,
        )

    def _parse_route_from_response(self, *, response: Any, user_query: str) -> RouterIntentRecognitionResult | None:
        choices = getattr(response, "choices", None) or []
        if not choices:
            return None

        message = getattr(choices[0], "message", None)
        if message is None:
            return None

        parsed_args = self._extract_tool_args(message)
        if not parsed_args:
            return None

        try:
            normalized = self._normalize_route_args(parsed_args=parsed_args, user_query=user_query)
            return RouterIntentRecognitionResult(
                user_query=user_query,
                intent_type=normalized["intent_type"],
                intent_confidence=normalized["intent_confidence"],
                slots=normalized["slots"],
                missing_slots=normalized["missing_slots"],
                target_agent=normalized["target_agent"],
                target_tool=normalized["target_tool"],
                tool_args=normalized["tool_args"],
                need_clarification=normalized["need_clarification"],
                clarification_content=normalized["clarification_content"],
                is_out_of_domain=normalized["is_out_of_domain"],
            )
        except Exception:
            return None

    def _normalize_route_args(self, *, parsed_args: dict[str, Any], user_query: str) -> dict[str, Any]:
        intent_type = self._normalize_intent(parsed_args.get("intent_type") or parsed_args.get("intent"))
        intent_confidence = max(
            0.0,
            min(1.0, float(parsed_args.get("intent_confidence", parsed_args.get("confidence", 0.0)))),
        )

        extracted_slots = self._extract_entity_slots(user_query)
        llm_slots = parsed_args.get("slots") or {}
        slots = {**extracted_slots, **llm_slots}

        function_call = parsed_args.get("function_call") or {}
        tool_args = parsed_args.get("tool_args")
        if tool_args is None and isinstance(function_call, dict):
            tool_args = function_call.get("args")
        if tool_args is None:
            tool_args = {}
        requires_confirmation = bool(parsed_args.get("need_confirmation", False)) or intent_type in {
            UserIntentEnum.SEND_NOTICE,
            UserIntentEnum.CREATE_TASK,
            UserIntentEnum.EXPORT_REPORT,
        }
        tool_args = {
            **self._build_tool_args(
                intent=intent_type,
                slots=slots,
                requires_confirmation=requires_confirmation,
            ),
            **tool_args,
        }
        if requires_confirmation:
            tool_args["requires_confirmation"] = True

        target_agent = str(parsed_args.get("target_agent") or self._default_target_agent(intent_type))
        target_tool = parsed_args.get("target_tool")
        if target_tool is None and isinstance(function_call, dict):
            target_tool = function_call.get("name")
        target_tool = target_tool or self._default_target_tool(intent_type)

        missing_slots = parsed_args.get("missing_slots") or []
        if intent_type in {UserIntentEnum.SEND_NOTICE, UserIntentEnum.CREATE_TASK, UserIntentEnum.EXPORT_REPORT}:
            missing_slots = sorted(set(missing_slots + self._missing_slots_for_write(intent=intent_type, slots=slots)))

        clarification_content = (
            parsed_args.get("clarification_content")
            or parsed_args.get("clarification_question")
            or ("请补充你的具体需求，我再继续处理。" if parsed_args.get("need_clarification") else None)
        )

        return {
            "intent_type": intent_type,
            "intent_confidence": intent_confidence,
            "slots": slots,
            "missing_slots": missing_slots,
            "target_agent": target_agent,
            "target_tool": target_tool,
            "tool_args": tool_args,
            "need_clarification": bool(parsed_args.get("need_clarification", False)),
            "clarification_content": clarification_content,
            "is_out_of_domain": bool(parsed_args.get("is_out_of_domain", False)) or intent_type == UserIntentEnum.OUT_OF_DOMAIN,
        }

    def _normalize_intent(self, raw_intent: Any) -> UserIntentEnum:
        intent = str(raw_intent or "").strip()
        legacy_mapping = {
            IntentType.GREETING.value: UserIntentEnum.NEED_CLARIFICATION,
            IntentType.QUERY_VIOLATION.value: UserIntentEnum.QUERY_DETAIL,
            IntentType.QUERY_REPORT.value: UserIntentEnum.QUERY_SUMMARY,
            IntentType.DISPATCH_ACTION.value: UserIntentEnum.SEND_NOTICE,
            IntentType.COMPLIANCE_CONSULT.value: UserIntentEnum.QUERY_DETAIL,
            IntentType.UNKNOWN.value: UserIntentEnum.NEED_CLARIFICATION,
        }
        if intent in legacy_mapping:
            return legacy_mapping[intent]
        return UserIntentEnum(intent)

    def _extract_entity_slots(self, message: str) -> dict[str, Any]:
        text = message or ""
        slots: dict[str, Any] = {}
        alert_match = self._ALERT_ID_PATTERN.search(text)
        event_match = self._EVENT_ID_PATTERN.search(text)
        task_match = self._TASK_ID_PATTERN.search(text)
        if alert_match:
            slots["alert_id"] = alert_match.group(0).upper()
        if event_match:
            slots["event_id"] = event_match.group(0).upper()
        if task_match:
            slots["task_id"] = task_match.group(0).upper()
        slots["entity_boundary"] = {
            "has_alert_id": "alert_id" in slots,
            "has_event_id": "event_id" in slots,
            "has_task_id": "task_id" in slots,
            "dual_entity": "alert_id" in slots and "event_id" in slots,
        }
        return slots

    def _build_tool_args(
        self,
        *,
        intent: UserIntentEnum,
        slots: dict[str, Any],
        requires_confirmation: bool,
    ) -> dict[str, Any]:
        args: dict[str, Any] = {
            "scene": self._scene_for_intent(intent=intent, slots=slots).value,
            "requires_confirmation": requires_confirmation,
        }
        for key in ("alert_id", "event_id", "task_id"):
            if key in slots:
                args[key] = slots[key]
        if requires_confirmation:
            args["action_type"] = self._action_type_for_intent(intent)
        return args

    def _scene_for_intent(self, *, intent: UserIntentEnum, slots: dict[str, Any]) -> QuerySceneEnum:
        if "event_id" in slots:
            return QuerySceneEnum.EVENT_QUERY
        if intent == UserIntentEnum.QUERY_RECTIFICATION or "task_id" in slots:
            return QuerySceneEnum.RECTIFICATION_QUERY
        if intent in {UserIntentEnum.QUERY_SUMMARY, UserIntentEnum.QUERY_TREND, UserIntentEnum.QUERY_RANKING}:
            return QuerySceneEnum.STATISTICS_QUERY
        return QuerySceneEnum.ALARM_QUERY

    @staticmethod
    def _default_target_agent(intent: UserIntentEnum) -> str:
        if intent in {UserIntentEnum.SEND_NOTICE, UserIntentEnum.CREATE_TASK, UserIntentEnum.EXPORT_REPORT}:
            return TargetAgent.TRIAGE_AGENT.value
        if intent in {UserIntentEnum.NEED_CLARIFICATION, UserIntentEnum.OUT_OF_DOMAIN}:
            return TargetAgent.ROUTER_AGENT.value
        return TargetAgent.DATA_AGENT.value

    @staticmethod
    def _default_target_tool(intent: UserIntentEnum) -> str:
        if intent in {UserIntentEnum.SEND_NOTICE, UserIntentEnum.CREATE_TASK, UserIntentEnum.EXPORT_REPORT}:
            return "preview_dispatch_action"
        if intent == UserIntentEnum.OUT_OF_DOMAIN:
            return "refuse_out_of_domain"
        if intent == UserIntentEnum.NEED_CLARIFICATION:
            return "request_clarification"
        return "query_food_safety_data"

    @staticmethod
    def _action_type_for_intent(intent: UserIntentEnum) -> str:
        if intent == UserIntentEnum.EXPORT_REPORT:
            return "export_report"
        if intent == UserIntentEnum.CREATE_TASK:
            return "create_task"
        return "send_notice"

    @staticmethod
    def _missing_slots_for_write(*, intent: UserIntentEnum, slots: dict[str, Any]) -> list[str]:
        if intent == UserIntentEnum.EXPORT_REPORT:
            return []
        if "event_id" in slots or "alert_id" in slots or "task_id" in slots:
            return []
        return ["alert_id_or_event_id"]

    @staticmethod
    def _extract_tool_args(message: Any) -> dict[str, Any] | None:
        tool_calls = getattr(message, "tool_calls", None) or []
        if tool_calls:
            first_call = tool_calls[0]
            function_obj = getattr(first_call, "function", None)
            arguments = getattr(function_obj, "arguments", None) if function_obj else None
            if isinstance(arguments, str):
                try:
                    return json.loads(arguments)
                except json.JSONDecodeError:
                    return None

        content = getattr(message, "content", None)
        if isinstance(content, str):
            content = content.strip()
            if content.startswith("{") and content.endswith("}"):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return None
        return None

    def is_low_confidence(self, result: IntentRecognitionResult) -> bool:
        return result.intent_confidence < self.LOW_CONFIDENCE_THRESHOLD or result.need_clarification

    def needs_confirmation(self, result: IntentRecognitionResult) -> bool:
        return result.intent_type in {
            UserIntentEnum.SEND_NOTICE,
            UserIntentEnum.CREATE_TASK,
            UserIntentEnum.EXPORT_REPORT,
        }

    def _load_system_prompt(self) -> str:
        if not self._SYSTEM_PROMPT_FILE.exists():
            return ""
        return self._SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)


__all__ = ["RouterService", "RouterIntentRecognitionResult", "TargetAgent", "IntentType"]
