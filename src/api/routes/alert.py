"""
边缘告警 Webhook 网关实现 (alert.py)

面向 EdgeAgent 与前端/内部服务的告警数据接口。
所有外部输入/输出必须符合 src/core/schemas.py 定义，禁止私自扩展字段。

设计约束：
- 不绑定特定 Web 框架，提供纯异步函数，可被 FastAPI/Flask/其他框架直接调用。
- 存储层通过 AlertStorage 抽象接口注入，默认提供内存实现（Week1 开发/测试用）。
- 文件存储、数据库、消息总线均为可替换组件，通过构造函数或环境配置注入。

规范来源: docs/全局JSON-Schema规范.md V1.0
docs/告警数据格式.md
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import re
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from pydantic import ValidationError

from src.core.schemas import (
    AlertCoreModel,
    AlertDetailResponse,
    AlertLevelEnum,
    AlertListQueryRequest,
    AlertListQueryResponse,
    AlertPushRequest,
    AlertPushResponse,
    BEIJING_TZ,
    EventDetailResponse,
    EventListQueryResponse,
    RectificationStatusEnum,
    VerifyResultEnum,
    ViolationEventModel,
    ViolationTypeEnum,
    beijing_now,
    generate_id,
)
from src.core.exceptions import (
    ErrorCodeEnum,
    EdgeAlertPushFailedError,
    GatewayRequestInvalidError,
    ParamError,
    PermissionDeniedError,
    DBResultEmptyError,
    StorageFailedError,
)
from src.core.logger import log, TraceContext
from src.core.config import jwt_settings


# ---------------------------------------------------------------------------
# 常量与配置
# ---------------------------------------------------------------------------

# 边缘盒子 API Key 白名单，从环境变量读取，逗号分隔
_EDGE_AGENT_API_KEYS = os.getenv("EDGE_AGENT_API_KEYS", "").split(",")
_EDGE_AGENT_API_KEYS = {k.strip() for k in _EDGE_AGENT_API_KEYS if k.strip()}

# 告警截图存储路径
_ALERT_IMAGE_DIR = Path(os.getenv("ALERT_IMAGE_DIR", "/app/alert_images"))

# 文件限制
_MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
_MAX_IMAGE_WIDTH = 4096
_MAX_IMAGE_HEIGHT = 2160

# 魔数白名单
_IMAGE_MAGIC_NUMBERS = {
    b"\xFF\xD8\xFF": "jpeg",
    b"\x89\x50\x4E\x47": "png",
}

# 时间解析格式（EdgeAgent 推送的 naive 时间字符串）
_ALERT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


# ---------------------------------------------------------------------------
# 存储层抽象接口
# ---------------------------------------------------------------------------

class AlertStorage(ABC):
    """告警数据存储抽象接口。

    Week1 默认提供 InMemoryAlertStorage 内存实现；Week2~Week3 可替换为
    MySQLStorage / MongoStorage 等持久化实现，业务代码无需修改。
    """

    @abstractmethod
    async def save_alert(self, alert: AlertCoreModel) -> None:
        """保存单条告警，若 alert.id 已存在则覆盖。"""

    @abstractmethod
    async def get_alert(self, alert_id: str) -> Optional[AlertCoreModel]:
        """按 alert_id 查询单条告警，不存在返回 None。"""

    @abstractmethod
    async def list_alerts(
        self,
        *,
        store_scope: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        violation_type: Optional[List[ViolationTypeEnum]] = None,
        risk_level: Optional[List[AlertLevelEnum]] = None,
        rectification_status: Optional[List[RectificationStatusEnum]] = None,
        page_num: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AlertCoreModel], int]:
        """分页查询告警列表。

        Returns:
            (当前页数据列表, 符合条件的总条数)
        """

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[ViolationEventModel]:
        """按 event_id 查询单条违规事件，不存在返回 None。"""

    @abstractmethod
    async def list_events(
        self,
        *,
        store_scope: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        violation_type: Optional[List[ViolationTypeEnum]] = None,
        risk_level: Optional[List[AlertLevelEnum]] = None,
        rectification_status: Optional[List[RectificationStatusEnum]] = None,
        page_num: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ViolationEventModel], int]:
        """分页查询违规事件列表。"""


class InMemoryAlertStorage(AlertStorage):
    """内存存储实现，仅用于 Week1 开发/测试阶段。"""

    def __init__(self) -> None:
        self._alerts: Dict[str, AlertCoreModel] = {}
        self._events: Dict[str, ViolationEventModel] = {}
        self._lock = asyncio.Lock()

    async def save_alert(self, alert: AlertCoreModel) -> None:
        async with self._lock:
            self._alerts[alert.id] = alert

    async def get_alert(self, alert_id: str) -> Optional[AlertCoreModel]:
        async with self._lock:
            return self._alerts.get(alert_id)

    async def list_alerts(
        self,
        *,
        store_scope: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        violation_type: Optional[List[ViolationTypeEnum]] = None,
        risk_level: Optional[List[AlertLevelEnum]] = None,
        rectification_status: Optional[List[RectificationStatusEnum]] = None,
        page_num: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AlertCoreModel], int]:
        async with self._lock:
            items = list(self._alerts.values())
        items = self._filter_items(
            items,
            store_scope=store_scope,
            time_range=time_range,
            violation_type=violation_type,
            risk_level=risk_level,
            rectification_status=rectification_status,
        )
        total = len(items)
        start = (page_num - 1) * page_size
        end = start + page_size
        return items[start:end], total

    async def get_event(self, event_id: str) -> Optional[ViolationEventModel]:
        async with self._lock:
            return self._events.get(event_id)

    async def list_events(
        self,
        *,
        store_scope: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        violation_type: Optional[List[ViolationTypeEnum]] = None,
        risk_level: Optional[List[AlertLevelEnum]] = None,
        rectification_status: Optional[List[RectificationStatusEnum]] = None,
        page_num: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ViolationEventModel], int]:
        async with self._lock:
            items = list(self._events.values())
        items = self._filter_items(
            items,
            store_scope=store_scope,
            time_range=time_range,
            violation_type=violation_type,
            risk_level=risk_level,
            rectification_status=rectification_status,
        )
        total = len(items)
        start = (page_num - 1) * page_size
        end = start + page_size
        return items[start:end], total

    @staticmethod
    def _filter_items(
        items: List[Any],
        store_scope: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        violation_type: Optional[List[ViolationTypeEnum]] = None,
        risk_level: Optional[List[AlertLevelEnum]] = None,
        rectification_status: Optional[List[RectificationStatusEnum]] = None,
    ) -> List[Any]:
        """通用过滤逻辑，适用于 AlertCoreModel 和 ViolationEventModel。"""
        result = items
        if store_scope is not None:
            result = [i for i in result if getattr(i, "store_id", None) in store_scope]
        if time_range is not None:
            start, end = time_range
            result = [i for i in result if start <= i.timestamp <= end]
        if violation_type is not None:
            result = [i for i in result if getattr(i, "violation_type", None) in violation_type]
        if risk_level is not None:
            result = [i for i in result if getattr(i, "level", None) in risk_level]
        if rectification_status is not None:
            result = [i for i in result if getattr(i, "rectification_status", None) in rectification_status]
        # 默认按时间倒序
        result = sorted(result, key=lambda x: x.timestamp, reverse=True)
        return result


# ---------------------------------------------------------------------------
# 网关服务类
# ---------------------------------------------------------------------------

class AlertGatewayService:
    """边缘告警网关服务。

    职责边界：
    - 入参校验、文件安全校验、API Key 校验
    - 数据格式转换（naive 时间转 aware、level 字符串映射枚举）
    - 截图持久化（生成 image_url）
    - 告警入库（通过 AlertStorage）
    - 消息总线事件投递（ALERT_RECEIVED）
    - 审计日志埋点

    不负责：
    - 业务规则判定（如是否违规、风险等级调整）——由监管 Agent 处理
    - 数据库连接池管理——由具体 AlertStorage 实现负责
    """

    def __init__(
        self,
        storage: Optional[AlertStorage] = None,
        image_dir: Optional[Path] = None,
        api_keys: Optional[set[str]] = None,
    ) -> None:
        self._storage = storage or InMemoryAlertStorage()
        self._image_dir = image_dir or _ALERT_IMAGE_DIR
        self._api_keys = api_keys or _EDGE_AGENT_API_KEYS
        self._message_bus: Any = None

    # ------------------------------------------------------------------
    # 接口 1: EdgeAgent → 网关 告警推送
    # ------------------------------------------------------------------

    async def post_alert_push(
        self,
        alert_data: str,
        file: Optional[bytes] = None,
        x_api_key: str = "",
    ) -> AlertPushResponse:
        """EdgeAgent 推送告警到网关。"""
        trace_id = TraceContext.get_trace_id()

        # 1. API Key 校验（无效时不记录业务日志，避免恶意刷日志）
        if not x_api_key or x_api_key not in self._api_keys:
            log.warning("EdgeAgent API Key 无效，拒绝请求")
            raise GatewayRequestInvalidError(
                error_code=ErrorCodeEnum.GATEWAY_REQUEST_INVALID,
                message="X-API-KEY 缺失或无效",
            )

        # 2. 解析 alert_data JSON
        if not alert_data:
            raise ParamError(
                error_code=ErrorCodeEnum.PARAM_ERROR,
                message="alert_data 缺失",
            )

        try:
            raw_payload = json.loads(alert_data)
        except json.JSONDecodeError as exc:
            raise EdgeAlertPushFailedError(
                error_code=ErrorCodeEnum.EDGE_ALERT_PUSH_FAILED,
                message=f"alert_data JSON 解析失败: {exc}",
            )

        # 3. 字段完整性校验（camera_id, message, level, confidence, timestamp 必填）
        required_fields = ["camera_id", "message", "level", "confidence", "timestamp"]
        missing = [f for f in required_fields if f not in raw_payload or raw_payload[f] in (None, "")]
        if missing:
            raise EdgeAlertPushFailedError(
                error_code=ErrorCodeEnum.EDGE_ALERT_PUSH_FAILED,
                message=f"alert_data 必填字段缺失: {missing}",
            )

        # 4. 文件安全校验（如有上传）
        image_url: Optional[str] = None
        if file:
            image_url = await self._save_alert_image(file)

        # 5. 数据转换：naive 或 aware 时间字符串 → Aware Datetime（统一为北京时间）
        try:
            raw_ts = raw_payload["timestamp"]
            # 先尝试 ISO 8601 / fromisoformat（支持带时区）
            if "+" in raw_ts or "-" in raw_ts[10:] or raw_ts.endswith("Z"):
                raw_ts = raw_ts.replace("Z", "+00:00")
                aware_dt = datetime.fromisoformat(raw_ts)
                # 统一转换为北京时间
                aware_dt = aware_dt.astimezone(BEIJING_TZ)
            else:
                naive_dt = datetime.strptime(raw_ts, _ALERT_TIMESTAMP_FORMAT)
                aware_dt = naive_dt.replace(tzinfo=BEIJING_TZ)
        except ValueError as exc:
            raise EdgeAlertPushFailedError(
                error_code=ErrorCodeEnum.EDGE_ALERT_PUSH_FAILED,
                message=f"timestamp 格式非法，期望 '{_ALERT_TIMESTAMP_FORMAT}' 或 ISO 8601: {exc}",
            )

        # 6. level 字符串映射为 AlertLevelEnum（无法映射时兜底为 UNKNOWN，记录 warn）
        level_str = str(raw_payload.get("level", "")).lower().strip()
        try:
            level = AlertLevelEnum(level_str)
        except ValueError:
            level = AlertLevelEnum.UNKNOWN
            log.warning(f"level 值 '{level_str}' 无法映射为 AlertLevelEnum，已兜底为 UNKNOWN")

        # 7. violation_type 解析（EdgeAgent 推送的是字符串，需映射为枚举）
        violation_type = self._parse_violation_type(raw_payload.get("message", ""))

        # 8. 生成告警 ID
        alert_id = generate_id("ALT")

        # 9. 构建 AlertCoreModel
        alert = AlertCoreModel(
            id=alert_id,
            camera_id=raw_payload["camera_id"],
            camera_name=raw_payload.get("camera_name"),
            store_id=raw_payload.get("store_id"),
            location=raw_payload.get("location"),
            message=raw_payload["message"],
            violation_type=violation_type,
            level=level,
            confidence=float(raw_payload["confidence"]),
            image_url=image_url,
            detection_tags=raw_payload.get("detection_tags"),
            bbox=raw_payload.get("bbox"),
            timestamp=aware_dt,
        )

        # 10. 入库（必须先完成数据库入库，再写入消息总线）
        try:
            await self._storage.save_alert(alert)
        except Exception as exc:
            log.error(f"告警入库失败: {exc}")
            raise StorageFailedError(
                error_code=ErrorCodeEnum.STORAGE_FAILED,
                message=f"告警入库失败: {exc}",
            )

        # 11. 审计日志
        log.audit(
            f"告警推送成功 | alert_id={alert_id} | camera_id={alert.camera_id} | "
            f"level={level.value} | violation_type={violation_type.value}"
        )

        # 12. 写入消息总线（ALERT_RECEIVED 事件）—— 异步投递，失败不阻塞响应
        await self._publish_alert_received(alert)

        # 13. 构造响应
        return AlertPushResponse(
            code=ErrorCodeEnum.SUCCESS.value,
            message="告警推送成功",
            success=True,
            data={"alert_id": alert_id},
        )

    # ------------------------------------------------------------------
    # 接口 2: 查询告警详情
    # ------------------------------------------------------------------

    async def get_alert_detail(
        self,
        alert_id: str,
        authorization: str = "",
    ) -> AlertDetailResponse:
        """查询单条告警详情。"""
        # 解析权限上下文
        permission = self._parse_jwt(authorization)

        # 查询告警
        alert = await self._storage.get_alert(alert_id)
        if alert is None:
            raise DBResultEmptyError(
                error_code=ErrorCodeEnum.DB_RESULT_EMPTY,
                message=f"告警不存在: {alert_id}",
            )

        # 权限校验
        self._check_store_permission(permission, alert.store_id)

        # 审计日志
        log.audit(f"查询告警详情 | alert_id={alert_id} | user_id={permission.get('user_id')}")

        return AlertDetailResponse(
            code=ErrorCodeEnum.SUCCESS.value,
            message="查询成功",
            success=True,
            alert_detail=alert,
        )

    # ------------------------------------------------------------------
    # 接口 3: 查询告警列表
    # ------------------------------------------------------------------

    def _prepare_list_params(
        self,
        authorization: str,
        time_range_start: Optional[str],
        time_range_end: Optional[str],
        store_scope: Optional[List[str]],
        violation_type: Optional[List[str]],
        risk_level: Optional[List[str]],
        rectification_status: Optional[List[str]],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """解析并返回列表查询的通用参数和权限信息。"""
        permission = self._parse_jwt(authorization)
        effective_store_scope = self._effective_store_scope(permission, store_scope)
        time_range = self._parse_time_range(time_range_start, time_range_end)
        vtypes = self._parse_enum_list(violation_type, ViolationTypeEnum) if violation_type else None
        levels = self._parse_enum_list(risk_level, AlertLevelEnum) if risk_level else None
        rstatus = self._parse_enum_list(rectification_status, RectificationStatusEnum) if rectification_status else None
        return permission, {
            "store_scope": effective_store_scope,
            "time_range": time_range,
            "violation_type": vtypes,
            "risk_level": levels,
            "rectification_status": rstatus,
        }

    @staticmethod
    def _pagination_meta(total: int, page_num: int, page_size: int) -> dict[str, Any]:
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return {"total": total, "page_num": page_num, "page_size": page_size, "total_pages": total_pages}

    async def get_alert_list(
        self,
        authorization: str = "",
        time_range_start: Optional[str] = None,
        time_range_end: Optional[str] = None,
        store_scope: Optional[List[str]] = None,
        violation_type: Optional[List[str]] = None,
        risk_level: Optional[List[str]] = None,
        rectification_status: Optional[List[str]] = None,
        page_num: int = 1,
        page_size: int = 20,
    ) -> AlertListQueryResponse:
        """分页查询告警列表。"""
        permission, params = self._prepare_list_params(
            authorization, time_range_start, time_range_end,
            store_scope, violation_type, risk_level, rectification_status,
        )
        items, total = await self._storage.list_alerts(**params, page_num=page_num, page_size=page_size)
        meta = self._pagination_meta(total, page_num, page_size)
        log.audit(
            f"查询告警列表 | user_id={permission.get('user_id')} | total={total} | "
            f"page={page_num}/{meta['total_pages']}"
        )
        return AlertListQueryResponse(
            code=ErrorCodeEnum.SUCCESS.value, message="查询成功", success=True, items=items, **meta,
        )

    # ------------------------------------------------------------------
    # 接口 4: 查询违规事件详情
    # ------------------------------------------------------------------

    async def get_event_detail(
        self,
        event_id: str,
        authorization: str = "",
    ) -> EventDetailResponse:
        """查询单条违规事件详情（含 VLM 二次校验结论）。"""
        permission = self._parse_jwt(authorization)

        event = await self._storage.get_event(event_id)
        if event is None:
            raise DBResultEmptyError(
                error_code=ErrorCodeEnum.DB_RESULT_EMPTY,
                message=f"违规事件不存在: {event_id}",
            )

        self._check_store_permission(permission, event.store_id)

        log.audit(f"查询违规事件详情 | event_id={event_id} | user_id={permission.get('user_id')}")

        return EventDetailResponse(
            code=ErrorCodeEnum.SUCCESS.value,
            message="查询成功",
            success=True,
            event_detail=event,
        )

    # ------------------------------------------------------------------
    # 接口 5: 查询违规事件列表
    # ------------------------------------------------------------------

    async def get_event_list(
        self,
        authorization: str = "",
        time_range_start: Optional[str] = None,
        time_range_end: Optional[str] = None,
        store_scope: Optional[List[str]] = None,
        violation_type: Optional[List[str]] = None,
        risk_level: Optional[List[str]] = None,
        rectification_status: Optional[List[str]] = None,
        page_num: int = 1,
        page_size: int = 20,
    ) -> EventListQueryResponse:
        """分页查询违规事件列表（含 VLM 校验结论）。"""
        permission, params = self._prepare_list_params(
            authorization, time_range_start, time_range_end,
            store_scope, violation_type, risk_level, rectification_status,
        )
        items, total = await self._storage.list_events(**params, page_num=page_num, page_size=page_size)
        meta = self._pagination_meta(total, page_num, page_size)
        log.audit(
            f"查询违规事件列表 | user_id={permission.get('user_id')} | total={total} | "
            f"page={page_num}/{meta['total_pages']}"
        )
        return EventListQueryResponse(
            code=ErrorCodeEnum.SUCCESS.value, message="查询成功", success=True, items=items, **meta,
        )

    # ------------------------------------------------------------------
    # 内部工具方法
    # ------------------------------------------------------------------

    async def _save_alert_image(self, file_data: bytes) -> str:
        """保存告警截图到本地存储，返回相对路径 image_url。

        校验流程：
        1. 魔数校验（仅 JPEG/PNG）
        2. 大小限制（≤ 5MB）
        3. 分辨率限制（≤ 4096×2160）
        """
        if not file_data:
            raise ParamError(
                error_code=ErrorCodeEnum.PARAM_ERROR,
                message="上传文件为空",
            )

        if len(file_data) > _MAX_IMAGE_SIZE_BYTES:
            raise ParamError(
                error_code=ErrorCodeEnum.PARAM_ERROR,
                message=f"截图大小超限: {len(file_data)} bytes > {_MAX_IMAGE_SIZE_BYTES} bytes (5MB)",
            )

        # 魔数校验
        file_ext = None
        for magic, ext in _IMAGE_MAGIC_NUMBERS.items():
            if file_data.startswith(magic):
                file_ext = ext
                break
        if file_ext is None:
            raise ParamError(
                error_code=ErrorCodeEnum.PARAM_ERROR,
                message="截图格式非法，仅支持 JPEG/PNG",
            )

        # 分辨率校验（尝试用 Pillow，若未安装则跳过）
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_data))
            w, h = img.size
            if w > _MAX_IMAGE_WIDTH or h > _MAX_IMAGE_HEIGHT:
                raise ParamError(
                    error_code=ErrorCodeEnum.PARAM_ERROR,
                    message=f"截图分辨率超限: {w}x{h} > {_MAX_IMAGE_WIDTH}x{_MAX_IMAGE_HEIGHT}",
                )
        except ImportError:
            log.debug("Pillow 未安装，跳过分辨率校验")
        except ParamError:
            raise
        except Exception as exc:
            log.warning(f"分辨率校验异常，跳过: {exc}")

        # 保存文件
        file_name = f"{uuid.uuid4().hex}.{file_ext}"
        save_dir = self._image_dir
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / file_name

        try:
            save_path.write_bytes(file_data)
        except OSError as exc:
            log.error(f"截图保存失败: {exc}")
            raise StorageFailedError(
                error_code=ErrorCodeEnum.STORAGE_FAILED,
                message=f"截图保存失败: {exc}",
            )

        # 返回相对路径作为 image_url
        return f"/alert_images/{file_name}"

    async def _ensure_message_bus(self) -> Any:
        """懒加载并复用 MessageBus 实例，避免重复创建连接。"""
        if self._message_bus is not None:
            return self._message_bus
        from src.core.message_bus import MessageBusFactory

        self._message_bus = MessageBusFactory.create("redis")
        try:
            await self._message_bus.start()
        except Exception as exc:
            log.warning(f"消息总线启动失败，告警投递降级为日志: {exc}")
            self._message_bus = None
        return self._message_bus

    async def _publish_alert_received(self, alert: AlertCoreModel) -> None:
        """将告警事件投递到消息总线（ALERT_RECEIVED）。

        异步投递，失败不阻塞 HTTP 响应，仅记录 warn 日志。
        MessageBus 实例通过 _ensure_message_bus() 懒加载并复用。
        """
        from src.core.schemas import AgentEventModel, AgentEventTypeEnum

        bus = await self._ensure_message_bus()
        if bus is None:
            return

        try:
            event = AgentEventModel(
                event_id=generate_id("EVT"),
                event_type=AgentEventTypeEnum.ALERT_RECEIVED,
                source_agent="infra",
                target_agent="triage_agent",
                payload=alert.model_dump(mode="json"),
            )
            await bus.send_message("agent_message_bus", event)
            log.debug(f"ALERT_RECEIVED 事件已投递 | alert_id={alert.id}")
        except Exception as exc:
            # 投递失败不阻断主流程，仅记录日志
            log.warning(f"ALERT_RECEIVED 事件投递失败（非阻塞）: {exc}")

    @staticmethod
    def _parse_violation_type(message: str) -> ViolationTypeEnum:
        """从告警描述中解析违规类型编码。

        EdgeAgent 推送的 message 格式通常为："[no_mask] 检测到: no_mask"
        通过正则提取方括号内的类型标识。
        """
        mapping = {
            "no_mask": ViolationTypeEnum.A01,
            "no_hat": ViolationTypeEnum.A02,
            "no_uniform": ViolationTypeEnum.A03,
            "rat": ViolationTypeEnum.A04,
            "smoking": ViolationTypeEnum.A05,
        }
        match = re.search(r"\[(\w+)\]", message)
        if match:
            key = match.group(1).lower().strip()
            return mapping.get(key, ViolationTypeEnum.A99)
        return ViolationTypeEnum.A99

    @staticmethod
    def _parse_jwt(authorization: str) -> Dict[str, Any]:
        """解析 JWT Token，提取用户权限信息。

        安全策略：
        1. 优先使用 pyjwt 进行签名验证（生产环境必须开启）。
        2. 若 JWT_SECRET 未配置且 jwt_disable_verify=True，回退到 JSON 解析
           （仅限开发/测试环境，通过环境变量 JWT_DISABLE_VERIFY=1 显式开启）。
        """
        token = AlertGatewayService._extract_bearer_token(authorization)

        if jwt_settings.jwt_secret and not jwt_settings.jwt_disable_verify:
            return AlertGatewayService._decode_verified_jwt(token)

        if jwt_settings.jwt_disable_verify:
            return AlertGatewayService._decode_dev_jwt(token)

        raise PermissionDeniedError(
            error_code=ErrorCodeEnum.PERMISSION_DENIED,
            message="JWT 验签未配置（缺少 JWT_SECRET 或 JWT_DISABLE_VERIFY）",
        )

    @staticmethod
    def _extract_bearer_token(authorization: str) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise PermissionDeniedError(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                message="Authorization 缺失或格式非法",
            )
        token = authorization[7:].strip()
        if not token:
            raise PermissionDeniedError(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                message="JWT Token 为空",
            )
        return token

    @staticmethod
    def _decode_verified_jwt(token: str) -> Dict[str, Any]:
        try:
            import jwt as pyjwt

            payload = pyjwt.decode(
                token,
                jwt_settings.jwt_secret,
                algorithms=[jwt_settings.jwt_algorithm],
                issuer=jwt_settings.jwt_issuer,
                audience=jwt_settings.jwt_audience,
            )
        except Exception as exc:
            raise PermissionDeniedError(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                message=f"JWT 验签失败: {exc}",
            ) from exc

        if not isinstance(payload, dict):
            raise PermissionDeniedError(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                message="JWT payload 格式非法",
            )
        return payload

    @staticmethod
    def _decode_dev_jwt(token: str) -> Dict[str, Any]:
        log.error("JWT 验签已禁用，使用 JSON 解析 fallback（仅限开发环境）")
        try:
            payload = json.loads(token)
        except json.JSONDecodeError as exc:
            raise PermissionDeniedError(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                message=f"JWT Token JSON 解析失败: {exc}",
            ) from exc

        if not isinstance(payload, dict):
            raise PermissionDeniedError(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                message="JWT Token payload 必须为 JSON 对象",
            )
        return payload

    @staticmethod
    def _check_store_permission(permission: Dict[str, Any], store_id: Optional[str]) -> None:
        """校验用户是否有权访问指定门店的数据。

        权限规则：
        - ENTERPRISE_ADMIN: 可查询全部
        - AREA_SUPERVISOR: 可查询其 region_ids 或 store_ids 范围内的门店
        - STORE_MANAGER: 仅可查询其 store_ids 范围内的门店
        """
        role = permission.get("role_type", "")
        if role == "enterprise_admin":
            return

        allowed_stores = set(permission.get("store_ids", []) or [])
        if role == "area_supervisor":
            # 督导同时拥有 store_ids 和 region_ids 权限
            allowed_regions = set(permission.get("region_ids", []) or [])
            if not allowed_stores and not allowed_regions:
                raise PermissionDeniedError(
                    error_code=ErrorCodeEnum.PERMISSION_DENIED,
                    message="督导用户未被分配任何门店或区域权限",
                )
            # TODO(Week2): 补充 region_ids -> store_ids 映射查询
            # 当前阶段：store_id 匹配任一权限即允许
            if store_id is None or store_id in allowed_stores:
                return
            # 若 store_id 不在 store_ids 中，但督导有 region_ids，
            # 暂时放行（待 region-store 映射表落地后严格校验）
            if allowed_regions:
                return
            raise PermissionDeniedError(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                message=f"用户无权限访问门店 {store_id} 的数据",
            )

        # STORE_MANAGER 及其他角色：仅检查 store_ids
        if store_id is None or store_id in allowed_stores:
            return

        raise PermissionDeniedError(
            error_code=ErrorCodeEnum.PERMISSION_DENIED,
            message=f"用户无权限访问门店 {store_id} 的数据",
        )

    @staticmethod
    def _effective_store_scope(
        permission: Dict[str, Any],
        requested_scope: Optional[List[str]],
    ) -> Optional[List[str]]:
        """计算有效的门店查询范围。

        - 若用户传入 store_scope，必须是其权限范围的子集；越权直接抛异常。
        - 若用户未传入，自动按用户权限填充。
        """
        role = permission.get("role_type", "")
        if role == "enterprise_admin":
            # 企业管理员不过滤门店范围
            return requested_scope

        allowed_stores = set(permission.get("store_ids", []) or [])

        if role == "area_supervisor":
            allowed_regions = set(permission.get("region_ids", []) or [])
            if not allowed_stores and not allowed_regions:
                raise PermissionDeniedError(
                    error_code=ErrorCodeEnum.PERMISSION_DENIED,
                    message="督导用户未被分配任何门店或区域权限",
                )
            # TODO(Week2): 补充 region_ids -> store_ids 映射，严格限定督导管辖范围
            effective_scope = list(allowed_stores)
            if requested_scope is not None:
                requested_set = set(requested_scope)
                # 督导的越权检查：store_scope 必须是其 store_ids 子集
                # （region_ids 映射完成后再加入 region 范围校验）
                if allowed_stores and not requested_set.issubset(allowed_stores):
                    # 若督导有 region_ids 但无具体 store_ids 映射，暂时放行
                    if not allowed_regions:
                        illegal = requested_set - allowed_stores
                        raise PermissionDeniedError(
                            error_code=ErrorCodeEnum.PERMISSION_DENIED,
                            message=f"store_scope 越权: {illegal}",
                        )
                return requested_scope
            return effective_scope or None

        # STORE_MANAGER 及其他角色
        if not allowed_stores:
            raise PermissionDeniedError(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                message="用户未被分配任何门店权限",
            )

        if requested_scope is not None:
            requested_set = set(requested_scope)
            if not requested_set.issubset(allowed_stores):
                illegal = requested_set - allowed_stores
                raise PermissionDeniedError(
                    error_code=ErrorCodeEnum.PERMISSION_DENIED,
                    message=f"store_scope 越权: {illegal}",
                )
            return requested_scope

        return list(allowed_stores)

    @staticmethod
    def _parse_time_range(
        start_str: Optional[str],
        end_str: Optional[str],
    ) -> Optional[Tuple[datetime, datetime]]:
        """解析 ISO 8601 时间范围字符串为 Aware Datetime 元组。"""
        if start_str is None and end_str is None:
            return None

        fmt = "%Y-%m-%dT%H:%M:%S"
        # 支持带时区后缀的格式
        alt_fmt = "%Y-%m-%dT%H:%M:%S%z"

        def _parse(s: str) -> datetime:
            for f in (alt_fmt, fmt):
                try:
                    return datetime.strptime(s, f)
                except ValueError:
                    continue
            # 兜底：尝试解析并附加北京时区
            try:
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=BEIJING_TZ)
                return dt
            except ValueError as exc:
                raise ParamError(
                    error_code=ErrorCodeEnum.PARAM_ERROR,
                    message=f"时间格式非法: {s}",
                ) from exc

        start = _parse(start_str) if start_str else datetime(1970, 1, 1, tzinfo=BEIJING_TZ)
        end = _parse(end_str) if end_str else beijing_now()
        return (start, end)

    @staticmethod
    def _parse_enum_list(values: List[str], enum_cls: type[Enum]) -> List[Enum]:
        """将字符串列表转换为枚举列表，无法映射的值跳过并记录 warn。"""
        result = []
        for v in values:
            try:
                result.append(enum_cls(v.lower().strip()))
            except ValueError:
                log.warning(f"枚举值 '{v}' 无法映射为 {enum_cls.__name__}，已跳过")
        return result


# ---------------------------------------------------------------------------
# 模块级便利函数（保持与旧契约兼容）
# ---------------------------------------------------------------------------

# 模块级默认服务实例，便于直接调用
_default_service: Optional[AlertGatewayService] = None


def _get_default_service() -> AlertGatewayService:
    global _default_service
    if _default_service is None:
        _default_service = AlertGatewayService()
    return _default_service


async def post_alert_push(
    alert_data: str,
    file: Optional[bytes] = None,
    x_api_key: str = "",
) -> AlertPushResponse:
    """EdgeAgent 推送告警到网关（便利函数）。"""
    return await _get_default_service().post_alert_push(alert_data, file, x_api_key)


async def get_alert_detail(
    alert_id: str,
    authorization: str = "",
) -> AlertDetailResponse:
    """查询单条告警详情（便利函数）。"""
    return await _get_default_service().get_alert_detail(alert_id, authorization)


async def get_alert_list(
    authorization: str = "",
    time_range_start: Optional[str] = None,
    time_range_end: Optional[str] = None,
    store_scope: Optional[List[str]] = None,
    violation_type: Optional[List[str]] = None,
    risk_level: Optional[List[str]] = None,
    rectification_status: Optional[List[str]] = None,
    page_num: int = 1,
    page_size: int = 20,
) -> AlertListQueryResponse:
    """分页查询告警列表（便利函数）。"""
    return await _get_default_service().get_alert_list(
        authorization,
        time_range_start,
        time_range_end,
        store_scope,
        violation_type,
        risk_level,
        rectification_status,
        page_num,
        page_size,
    )


async def get_event_detail(
    event_id: str,
    authorization: str = "",
) -> EventDetailResponse:
    """查询单条违规事件详情（便利函数）。"""
    return await _get_default_service().get_event_detail(event_id, authorization)


async def get_event_list(
    authorization: str = "",
    time_range_start: Optional[str] = None,
    time_range_end: Optional[str] = None,
    store_scope: Optional[List[str]] = None,
    violation_type: Optional[List[str]] = None,
    risk_level: Optional[List[str]] = None,
    rectification_status: Optional[List[str]] = None,
    page_num: int = 1,
    page_size: int = 20,
) -> EventListQueryResponse:
    """分页查询违规事件列表（便利函数）。"""
    return await _get_default_service().get_event_list(
        authorization,
        time_range_start,
        time_range_end,
        store_scope,
        violation_type,
        risk_level,
        rectification_status,
        page_num,
        page_size,
    )


__all__ = [
    "AlertGatewayService",
    "AlertStorage",
    "InMemoryAlertStorage",
    "post_alert_push",
    "get_alert_detail",
    "get_alert_list",
    "get_event_detail",
    "get_event_list",
]
