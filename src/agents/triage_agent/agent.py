"""监管研判 Agent (TriageAgent)

职责边界：
1. 订阅消息总线的 ALERT_RECEIVED 事件
2. 对原始告警进行去重判断（同一 camera + 同类型 + 时间窗口内）
3. 对去重后的告警调用 VLM 进行二次校验（图片级 false-positive 过滤）
4. 产出 ViolationEventModel，发布 VERIFY_COMPLETED / VERIFY_FAILED
5. 审计日志全链路埋点

设计约束：
- 必须继承 BaseAgent，遵循标准生命周期
- VLM 调用通过 AsyncVLMClient，禁止直接使用同步 OpenAI 客户端
- 所有异常必须包装为 ProjectBaseException 子类
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.agents.base_agent import BaseAgent
from src.core.config import llm_settings
from src.core.exceptions import (
    AgentHandleFailedError,
    ErrorCodeEnum,
    ProjectBaseException,
    VLMVerifyFailedError,
)
from src.core.logger import log, TraceContext
from src.core.schemas import (
    AgentEventModel,
    AgentEventTypeEnum,
    AlertCoreModel,
    AlertLevelEnum,
    SeverityLevelEnum,
    VerificationMethodEnum,
    VerifyResultEnum,
    ViolationEventModel,
    beijing_now,
    generate_id,
)
from src.core.vlm_client import AsyncVLMClient


# ---------------------------------------------------------------------------
# 常量与配置
# ---------------------------------------------------------------------------

# 去重时间窗口：同一 camera + 同类违规，N 分钟内视为重复
_DEDUP_TIME_WINDOW_MINUTES = 10

# VLM 默认校验 Prompt 模板路径
_VLM_PROMPT_FILE = Path(__file__).resolve().parents[2] / "prompts" / "triage_vlm_prompt.txt"

# VLM 默认校验 Prompt（fallback，当文件不存在时使用）
_DEFAULT_VLM_PROMPT = """\
你是一名食品安全监管专家。请仔细分析图片，判断是否存在以下违规行为：

1. 未佩戴口罩（no_mask）
2. 未佩戴工作帽（no_hat）
3. 未穿工作服（no_uniform）
4. 鼠患（rat_presence）
5. 吸烟（smoking）

请按以下 JSON 格式输出判断结果：
{
    "is_violation": true/false,
    "violation_type": "no_mask|no_hat|no_uniform|rat_presence|smoking|none",
    "confidence": 0.0~1.0,
    "reason": "判定依据的详细描述"
}

注意：
- 如果图片不清晰或无法判断，is_violation 设为 false，confidence 设为 0.0
- 必须输出合法的 JSON，不要添加 Markdown 代码块标记
"""


class TriageAgent(BaseAgent):
    """监管研判 Agent：YOLO 告警去重 + VLM 二次校验。"""

    # 熔断器配置（VLM 调用成本高，阈值相对宽松）
    FUSE_FAILURE_THRESHOLD = 5
    FUSE_RECOVERY_TIMEOUT = 120.0
    FUSE_HALF_OPEN_MAX_CALLS = 2

    def __init__(
        self,
        agent_id: str = "triage_agent_01",
        vlm_client: Optional[AsyncVLMClient] = None,
    ):
        super().__init__(agent_id=agent_id, agent_name="triage_agent")
        self._vlm_client = vlm_client
        self._vlm_prompt = self._load_vlm_prompt()
        # 内存去重缓存：key=(camera_id, violation_type) -> last_alert_timestamp
        # Week2~Week3 替换为 Redis / 数据库实现
        self._dedup_cache: Dict[tuple[str, str], datetime] = {}
        self._cache_lock = asyncio.Lock()

    async def run(self) -> None:
        """启动 Agent：订阅 ALERT_RECEIVED 事件。"""
        self.status = AgentStatus.RUNNING
        # 实际消息总线订阅由上层编排器调用 subscribe_topic 完成
        log.info(f"TriageAgent started | agent_id={self.agent_id}")

    async def _on_event(self, event: AgentEventModel) -> Any:
        """处理消息总线事件。

        当前仅处理 ALERT_RECEIVED 事件，其他事件忽略。
        """
        if event.event_type != AgentEventTypeEnum.ALERT_RECEIVED:
            log.debug(f"TriageAgent 忽略非告警事件: {event.event_type.value}")
            return {"handled": False, "reason": "event_type_not_supported"}

        payload = event.payload or {}

        # 直接从 payload 反序列化 AlertCoreModel，无需二次查询存储层
        try:
            alert = AlertCoreModel(**payload)
        except Exception as exc:
            log.warning(f"ALERT_RECEIVED 事件 payload 无法反序列化为 AlertCoreModel: {exc}")
            return {"handled": False, "reason": "invalid_payload"}

        alert_id = alert.id

        # trace_id 透传
        if event.trace_id:
            TraceContext.set_trace_id(event.trace_id)

        try:
            result = await self._process_alert(alert, event.trace_id)
            return {"handled": True, "result": result}
        except ProjectBaseException:
            raise
        except Exception as exc:
            log.error(f"TriageAgent 处理告警异常: {exc}")
            raise AgentHandleFailedError(
                message=f"TriageAgent 处理告警异常: {exc}",
                detail={"alert_id": alert_id, "trace_id": event.trace_id},
            ) from exc
        finally:
            TraceContext.clear_trace_id()

    # ------------------------------------------------------------------
    # 核心业务流程
    # ------------------------------------------------------------------

    async def _process_alert(self, alert: AlertCoreModel, trace_id: str) -> Dict[str, Any]:
        """单条告警处理主链路：去重 → VLM 校验 → 产出事件。"""
        alert_id = alert.id

        # 1. 去重判断（检查+更新在同一锁内完成，避免 TOCTOU 竞态）
        is_duplicate = await self._check_and_update_dedup(alert)
        if is_duplicate:
            log.audit(
                f"告警去重命中，跳过 | alert_id={alert_id} | "
                f"camera_id={alert.camera_id} | violation_type={alert.violation_type.value}",
                trace_id=trace_id,
            )
            await self.publish(
                AgentEventTypeEnum.ALERT_DEDUPED,
                {"alert_id": alert_id, "reason": "time_window_duplicate"},
                target_agent="router_agent",
            )
            return {"status": "deduped", "alert_id": alert_id}

        # 3. VLM 二次校验（图片存在时才调用）
        if not alert.image_url:
            log.warning(f"告警无图片，跳过 VLM 校验 | alert_id={alert_id}")
            # 无图告警降级为边缘规则判定
            event_result = await self._create_violation_event(
                alert=alert,
                verify_result=VerifyResultEnum.UNCERTAIN,
                vlm_confidence=None,
                method=VerificationMethodEnum.EDGE_RULE,
                trace_id=trace_id,
            )
            await self._publish_verify_completed(event_result, trace_id)
            return {"status": "edge_rule_fallback", "event_id": event_result.event_id}

        verify_result, vlm_confidence, determination_basis = await self._vlm_verify(
            alert, trace_id
        )

        # 4. 构建 ViolationEventModel 并落库
        event_result = await self._create_violation_event(
            alert=alert,
            verify_result=verify_result,
            vlm_confidence=vlm_confidence,
            method=VerificationMethodEnum.VLM,
            trace_id=trace_id,
            determination_basis=determination_basis,
        )

        # 5. 发布校验完成事件
        await self._publish_verify_completed(event_result, trace_id)

        return {
            "status": "verified",
            "alert_id": alert_id,
            "event_id": event_result.event_id,
            "is_violation_confirmed": event_result.is_violation_confirmed,
            "confidence": vlm_confidence,
        }

    # ------------------------------------------------------------------
    # VLM 二次校验
    # ------------------------------------------------------------------

    async def _vlm_verify(
        self,
        alert: AlertCoreModel,
        trace_id: str,
    ) -> tuple[VerifyResultEnum, Optional[float], Optional[str]]:
        """调用 VLM 对告警图片进行二次校验。

        Returns:
            (校验结果枚举, VLM置信度, 判定依据文字)
        """
        # 构造带业务上下文的 Prompt
        prompt = self._build_vlm_prompt(alert)

        #  lazy init VLM client
        client = self._vlm_client
        if client is None:
            client = AsyncVLMClient()
            self._vlm_client = client

        try:
            raw_response = await client.verify_image(
                image_url=alert.image_url,
                prompt=prompt,
                trace_id=trace_id,
                temperature=0.3,
                max_tokens=512,
            )
        except Exception as exc:
            log.error(f"VLM 调用失败 | alert_id={alert.id}: {exc}")
            raise VLMVerifyFailedError(
                message=f"VLM 二次校验调用失败: {exc}",
                detail={"alert_id": alert.id, "trace_id": trace_id, "image_url": alert.image_url},
            ) from exc

        # 解析 VLM 返回的 JSON
        return self._parse_vlm_response(raw_response, alert)

    def _build_vlm_prompt(self, alert: AlertCoreModel) -> str:
        """为 VLM 构建带业务上下文的校验 Prompt。"""
        base = self._vlm_prompt or _DEFAULT_VLM_PROMPT
        context = (
            f"\n\n业务上下文："
            f"\n- 摄像头位置: {alert.location or '未知'}"
            f"\n- 原始告警描述: {alert.message or '无'}"
            f"\n- YOLO 检出类型: {alert.violation_type.value if alert.violation_type else '未知'}"
            f"\n- YOLO 置信度: {alert.confidence:.2f}"
        )
        return base + context

    @staticmethod
    def _parse_vlm_response(
        raw_response: str,
        alert: AlertCoreModel,
    ) -> tuple[VerifyResultEnum, Optional[float], Optional[str]]:
        """解析 VLM 返回的 JSON 响应。

        期望格式：
        {
            "is_violation": true/false,
            "violation_type": "...",
            "confidence": 0.0~1.0,
            "reason": "..."
        }
        """
        if not raw_response:
            log.warning(f"VLM 返回空响应 | alert_id={alert.id}")
            return VerifyResultEnum.UNCERTAIN, None, "VLM 返回空响应"

        # 尝试提取 JSON
        json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if not json_match:
            log.warning(f"VLM 响应中未找到 JSON | alert_id={alert.id} | response={raw_response[:100]}")
            return VerifyResultEnum.UNCERTAIN, None, f"无法解析 VLM 响应: {raw_response[:100]}"

        try:
            import json

            data = json.loads(json_match.group())
        except json.JSONDecodeError as exc:
            log.warning(f"VLM 响应 JSON 解析失败 | alert_id={alert.id}: {exc}")
            return VerifyResultEnum.UNCERTAIN, None, f"JSON 解析失败: {raw_response[:100]}"

        is_violation = bool(data.get("is_violation", False))
        confidence = data.get("confidence")
        if isinstance(confidence, (int, float)):
            confidence = float(confidence)
        else:
            confidence = None

        reason = data.get("reason", "")

        if is_violation:
            return VerifyResultEnum.TRUE_VIOLATION, confidence, reason
        else:
            return VerifyResultEnum.FALSE_ALARM, confidence, reason

    # ------------------------------------------------------------------
    # 去重逻辑
    # ------------------------------------------------------------------

    @staticmethod
    def _make_dedup_key(alert: AlertCoreModel) -> tuple[str, str] | None:
        """生成去重缓存键。"""
        if not alert.camera_id or not alert.violation_type:
            return None
        return (alert.camera_id, alert.violation_type.value)

    async def _check_and_update_dedup(self, alert: AlertCoreModel) -> bool:
        """检查告警是否重复，并在非重复时原子更新缓存（单锁内完成，避免 TOCTOU）。"""
        key = self._make_dedup_key(alert)
        if key is None:
            return False
        now = alert.timestamp or beijing_now()
        async with self._cache_lock:
            last_time = self._dedup_cache.get(key)
            if last_time is not None and (now - last_time) < timedelta(minutes=_DEDUP_TIME_WINDOW_MINUTES):
                return True
            self._dedup_cache[key] = now
            return False

    # ------------------------------------------------------------------
    # 事件构建与发布
    # ------------------------------------------------------------------

    async def _create_violation_event(
        self,
        alert: AlertCoreModel,
        verify_result: VerifyResultEnum,
        vlm_confidence: Optional[float],
        method: VerificationMethodEnum,
        trace_id: str,
        determination_basis: Optional[str] = None,
    ) -> ViolationEventModel:
        """根据校验结果构建 ViolationEventModel。"""
        now = beijing_now()
        event_id = generate_id("EVT")

        is_confirmed = verify_result == VerifyResultEnum.TRUE_VIOLATION

        # severity_level 仅在有确认违规时判定
        severity = None
        if is_confirmed and alert.level:
            severity = SeverityLevelEnum(alert.level.value) if alert.level.value in {"high", "medium", "low", "critical"} else SeverityLevelEnum.MEDIUM

        log.audit(
            f"违规事件产出 | event_id={event_id} | alert_id={alert.id} | "
            f"is_confirmed={is_confirmed} | method={method.value} | confidence={vlm_confidence}",
            trace_id=trace_id,
        )

        return ViolationEventModel(
            alert_id=alert.id,
            camera_id=alert.camera_id,
            camera_location=alert.location,
            store_id=alert.store_id,
            message=alert.message or "",
            level=alert.level or AlertLevelEnum.UNKNOWN,
            confidence=alert.confidence,
            image_url=alert.image_url,
            detection_tags=alert.detection_tags,
            is_read=False,
            timestamp=alert.timestamp,
            created_at=now,
            event_id=event_id,
            is_violation_confirmed=is_confirmed,
            severity_level=severity,
            verified_image_url=alert.image_url or "",
            verification_method=method,
            vlm_confidence=vlm_confidence,
            model_version=llm_settings.llm_model_name,
            verified_at=now,
            determination_basis=determination_basis,
            aggregation_count=1,
            updated_at=now,
        )

    async def _publish_verify_completed(
        self,
        event: ViolationEventModel,
        trace_id: str,
    ) -> None:
        """发布 VERIFY_COMPLETED 事件到消息总线。"""
        log.debug(
            f"发布 VERIFY_COMPLETED 事件 | event_id={event.event_id} | trace_id={trace_id}"
        )
        await self.publish(
            AgentEventTypeEnum.VERIFY_COMPLETED,
            {
                "event_id": event.event_id,
                "alert_id": event.alert_id,
                "is_violation_confirmed": event.is_violation_confirmed,
                "confidence": event.vlm_confidence,
                "verification_method": event.verification_method.value,
            },
            target_agent="router_agent",
        )

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _load_vlm_prompt() -> str:
        """加载 VLM 校验 Prompt 文件。"""
        if _VLM_PROMPT_FILE.exists():
            return _VLM_PROMPT_FILE.read_text(encoding="utf-8").strip()
        return ""
