"""
全局Schema核心模块 (schemas.py)

基于 Pydantic V2 实现，定义全项目统一的数据模型、枚举、接口契约。
所有外部输入/输出必须符合本模块定义的结构，禁止私自修改核心字段。

规范来源: docs/全局JSON-Schema规范.md V1.0（正式版）
"""

from __future__ import annotations

import secrets
import string
import time
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# 通用工具函数
# ---------------------------------------------------------------------------

BEIJING_TZ = timezone(offset=timedelta(hours=8), name="Asia/Shanghai")


def beijing_now() -> datetime:
    """全项目统一时间生成函数，返回带北京时区的 Aware Datetime。

    禁止直接使用 datetime.now()（生成 Naive Datetime，会导致时区错乱）。
    """
    return datetime.now(BEIJING_TZ)


def generate_id(prefix: str, random_length: int = 8) -> str:
    """生成全局唯一ID，格式：{PREFIX}{13位毫秒时间戳}{random_length位随机字母数字}。

    设计演进：原方案使用 3 位大写字母（26^3 = 17,576 种组合），在边缘告警风暴场景
    （同一毫秒 20+ 张图）下冲突风险不可忽视。现方案改用 secrets 模块生成
    random_length 位字母数字混合随机串（36^8 ≈ 2.8 万亿），彻底消除分布式冲突。

    使用约束：random_length 不建议低于 6，默认 8。
    """
    timestamp = int(time.time() * 1000)
    alphabet = string.ascii_uppercase + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(random_length))
    return f"{prefix}{timestamp}{random_part}"


# ---------------------------------------------------------------------------
# 全局枚举
# ---------------------------------------------------------------------------

class UserRoleEnum(str, Enum):
    """全局用户角色枚举，路由/数据/权限模块通用"""
    STORE_MANAGER = "store_manager"
    AREA_SUPERVISOR = "area_supervisor"
    ENTERPRISE_ADMIN = "enterprise_admin"


class AlertLevelEnum(str, Enum):
    """全局告警级别枚举，边缘/监管/数据模块通用。

    UNKNOWN 兜底约束：网关层接收 EdgeAgent 推送的 level 字符串时，
    无法匹配的值统一映射为 UNKNOWN 并记录 warn 日志，不阻断告警主流程。
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class VerifyResultEnum(str, Enum):
    """VLM二次校验结果枚举，监管Agent专用"""
    TRUE_VIOLATION = "true_violation"
    FALSE_ALARM = "false_alarm"
    UNCERTAIN = "uncertain"


class ViolationTypeEnum(str, Enum):
    """全局违规类型枚举，监管/数据/路由模块通用。

    UNKNOWN 与 OTHER 语义差异：
    - OTHER (A99)：业务侧已识别为违规但未归入既有类目，需后续运营补类目；
    - UNKNOWN (A00)：网关层无法将外部输入映射到任何已知类目（含 OTHER），统一兜底。
    """
    NO_MASK = "A01"
    NO_HAT = "A02"
    NO_UNIFORM = "A03"
    RAT_PRESENCE = "A04"
    SMOKING = "A05"
    OTHER = "A99"
    UNKNOWN = "A00"


class UserIntentEnum(str, Enum):
    """全局用户意图枚举，路由/数据/监管模块通用"""
    QUERY_SUMMARY = "query_summary"
    QUERY_DETAIL = "query_detail"
    QUERY_TREND = "query_trend"
    QUERY_RANKING = "query_ranking"
    QUERY_RECTIFICATION = "query_rectification"
    EXPORT_REPORT = "export_report"
    SEND_NOTICE = "send_notice"
    CREATE_TASK = "create_task"
    CONFIRM_ACTION = "confirm_action"
    REJECT_ACTION = "reject_action"
    NEED_CLARIFICATION = "need_clarification"
    OUT_OF_DOMAIN = "out_of_domain"


class RectificationStatusEnum(str, Enum):
    """全局整改状态枚举，告警/监管/数据/路由模块通用。"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    EXPIRED = "expired"


class SeverityLevelEnum(str, Enum):
    """违规严重等级枚举，监管研判 Agent（A组）VLM 二次校验后专用，与 AlertLevelEnum 职责区分。

    职责边界：
    - AlertLevelEnum 描述 YOLO 初始告警级别（high / medium / low），来自边缘端推送；
    - SeverityLevelEnum 描述经 VLM 二次校验后确认的违规严重程度（critical / major / minor），
      仅当 is_violation_confirmed=True 时非空，误报场景必须为 null。
    """
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class VerificationMethodEnum(str, Enum):
    """校验方式枚举，监管研判 Agent（A组）专用。

    区分正常模式与降级模式，下游消费方必须据此区分结论可信度：
    - vlm：云端 VLM 视觉大模型校验，可信度高，正常业务首选；
    - edge_rule：边缘端规则校验，降级模式，云端异常时自动切换。
    """
    VLM = "vlm"
    EDGE_RULE = "edge_rule"


class AgentEventTypeEnum(str, Enum):
    """Agent 间通信事件类型枚举，基建消息总线全局唯一标准。

    强约束：所有通过消息总线发布/订阅的事件，event_type 必须为本枚举注册值；
    新增类型须经 Schema 变更申请单审批，禁止业务侧使用未注册字符串。
    """
    # 告警业务流转
    ALERT_RECEIVED = "alert_received"
    ALERT_DEDUPED = "alert_deduped"
    ALERT_DISPATCHED = "alert_dispatched"
    ALERT_VERIFIED = "alert_verified"
    # LLM/VLM 校验
    VERIFY_COMPLETED = "verify_completed"
    VERIFY_FAILED = "verify_failed"
    # 数据查询
    SQL_GENERATED = "sql_generated"
    SQL_EXECUTED = "sql_executed"
    SQL_BLOCKED = "sql_blocked"
    # 意图与路由
    INTENT_RECOGNIZED = "intent_recognized"
    ROUTE_DISPATCHED = "route_dispatched"
    ROUTE_COMPLETED = "route_completed"
    ROUTE_FAILED = "route_failed"
    # 用户交互
    USER_QUERY_RECEIVED = "user_query_received"
    USER_CONFIRMED = "user_confirmed"
    USER_REJECTED = "user_rejected"
    # 整改业务
    RECTIFICATION_CREATED = "rectification_created"
    RECTIFICATION_UPDATED = "rectification_updated"
    # 系统层
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_ERROR = "agent_error"
    SYSTEM_EVENT = "system_event"


class SqlGenerationStatusEnum(str, Enum):
    """SQL 生成状态枚举，数据Agent专用。"""
    SUCCESS = "success"
    EMPTY_RESPONSE = "empty_response"
    PARSE_ERROR = "parse_error"
    RETRY_EXHAUSTED = "retry_exhausted"


class DbExecuteStatusEnum(str, Enum):
    """数据库执行状态枚举，数据Agent / 基建拦截器通用。"""
    SUCCESS = "success"
    CONNECTION_FAILED = "connection_failed"
    QUERY_TIMEOUT = "query_timeout"
    PERMISSION_DENIED = "permission_denied"
    SYNTAX_ERROR = "syntax_error"


class AuditEventTypeEnum(str, Enum):
    """全局审计事件类型枚举"""
    # 用户操作类
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_QUERY = "user_query"
    USER_EXPORT = "user_export"
    USER_ACTION_CONFIRM = "user_action_confirm"
    USER_ACTION_REJECT = "user_action_reject"
    # 大模型调用类
    INTENT_RESOLVED = "intent_resolved"
    LLM_CALL = "llm_call"
    SQL_GENERATED = "sql_generated"
    VLM_VERIFY = "vlm_verify"
    # 工具调用类
    TOOL_CALLED = "tool_called"
    AGENT_ROUTE = "agent_route"
    DB_EXECUTE = "db_execute"
    # 安全拦截类
    SQL_SECURITY_BLOCKED = "sql_security_blocked"
    SQL_PERFORMANCE_BLOCKED = "sql_performance_blocked"
    PERMISSION_DENIED = "permission_denied"
    LLM_FUSE_TRIGGERED = "llm_fuse_triggered"
    # 告警业务类
    ALERT_RECEIVED = "alert_received"
    ALERT_VERIFIED = "alert_verified"
    RECTIFICATION_UPDATED = "rectification_updated"
    # 系统类
    CONFIRMATION_CREATED = "confirmation_created"
    CONFIRMATION_EXPIRED = "confirmation_expired"
    SYSTEM_ERROR = "system_error"


class ExecutionStatusEnum(str, Enum):
    """路由计划执行状态枚举，路由Agent专用。

    强约束：所有 RoutePlanModel.execution_status 必须使用本枚举，禁止业务代码自由拼写字符串。
    """
    PLANNED = "planned"
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ActionTypeEnum(str, Enum):
    """高危操作类型枚举，ConfirmationModel / 路由Agent专用。

    强约束：所有 ConfirmationModel.action_type 必须使用本枚举，禁止业务代码自由拼写字符串。
    """
    EXPORT_REPORT = "export_report"
    SEND_NOTICE = "send_notice"
    CREATE_TASK = "create_task"


class BlockedTypeEnum(str, Enum):
    """AST安全拦截类型枚举，数据Agent / 基建拦截器专用。

    强约束：所有 ASTSecurityCheckResult.blocked_type 必须使用本枚举。
    """
    DML = "DML"
    DDL = "DDL"
    MULTI_STATEMENT = "MULTI_STATEMENT"
    STORED_PROCEDURE = "STORED_PROCEDURE"
    FUNCTION_CALL = "FUNCTION_CALL"


class QuerySceneEnum(str, Enum):
    """数据查询场景枚举，FoodSafetyDataQueryRequest 专用。

    强约束：所有 scene 字段必须使用本枚举，新增场景须经 Schema 变更申请单审批。
    """
    ALARM_QUERY = "alarm_query"
    EVENT_QUERY = "event_query"
    RECTIFICATION_QUERY = "rectification_query"
    STATISTICS_QUERY = "statistics_query"


class PermissionActionEnum(str, Enum):
    """用户权限动作枚举，UserInfoModel / PermissionContext 专用。

    强约束：所有 permission_actions 列表元素必须使用本枚举，禁止业务代码自由拼写字符串。
    """
    QUERY_ALERT = "query_alert"
    EXPORT_REPORT = "export_report"
    SEND_NOTICE = "send_notice"
    CREATE_RECTIFICATION = "create_rectification"
    CONFIRM_ACTION = "confirm_action"
    VIEW_DATA = "view_data"


# ---------------------------------------------------------------------------
# 全链路追踪与通用基类
# ---------------------------------------------------------------------------

class TraceBase(BaseModel):
    """全链路追踪基类，所有核心模型必须继承，保障全链路可追溯。"""
    trace_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="全链路唯一追踪ID，全流程透传",
        min_length=32,
        max_length=32,
    )

    model_config = {"populate_by_name": True}


class RequestBase(TraceBase):
    """所有 HTTP/WS 接口请求基类"""
    user_id: str = Field(description="操作用户唯一ID")
    request_time: datetime = Field(
        default_factory=beijing_now,
        description="请求发起时间（Aware Datetime，带北京时区）",
    )


class ResponseBase(TraceBase):
    """所有 HTTP/WS 接口响应基类"""
    code: str = Field(description="全局统一响应码，0000为成功，其余为失败")
    message: str = Field(description="响应描述信息")
    success: bool = Field(description="请求是否成功")
    response_time: datetime = Field(
        default_factory=beijing_now,
        description="响应返回时间（Aware Datetime，带北京时区）",
    )
    data: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default=None, description="响应业务数据"
    )


class PageResponseBase(ResponseBase):
    """全项目通用分页响应基类，所有列表查询响应必须继承。

    使用约束：
    1. 列表数据字段统一命名为 items，由继承方按业务类型声明；
    2. 分页参数 page_num、page_size 与请求侧保持一致；
    3. total_pages 由后端基于 total 与 page_size 计算填充，前端禁止自行二次推导。
    """
    total: int = Field(description="符合条件的总条数", ge=0)
    page_num: int = Field(description="当前页码", ge=1)
    page_size: int = Field(description="每页条数", ge=1, le=100)
    total_pages: int = Field(description="总页数", ge=0)


class ChatMessage(BaseModel):
    """对话消息标准结构，用于 SessionContext.chat_history 及多轮对话上下文。

    替代原 List[Dict[str, Any]] 松散结构，提供类型安全与字段约束。
    """
    role: str = Field(description="消息角色：user / assistant / system")
    content: str = Field(description="消息内容文本")
    timestamp: datetime = Field(default_factory=beijing_now, description="消息发送时间")
    intent_type: Optional[UserIntentEnum] = Field(default=None, description="消息关联的用户意图（可选）")


# ---------------------------------------------------------------------------
# 告警数据核心模型
# ---------------------------------------------------------------------------

class EdgeAlertPayload(BaseModel):
    """EdgeAgent 原始 JSON payload（嵌入在 multipart 的 alert_data 字段中）。

    注意：此模型仅用于网关层接收和解析，不做枚举校验，最大限度兼容存量 EdgeAgent。
    """
    camera_id: str = Field(description="摄像头唯一标识")
    message: str = Field(description="告警描述，固定格式[{model_name}] 检测到: {class_name}")
    level: str = Field(description="告警级别原始字符串（high/medium/low 等）")
    confidence: float = Field(description="YOLO推理置信度", ge=0.0, le=1.0)
    timestamp: str = Field(description="原始时间字符串，格式为 'YYYY-MM-DD HH:MM:SS.ffffff'，无时区后缀")
    detection_tags: Optional[str] = Field(default=None, description="检测标签扩展字段")


class AlertPushRequest(TraceBase):
    """基建网关解析 EdgeAgent 推送后的内部模型。

    网关层职责：
    1. 解析 multipart，提取 alert_data JSON 和 file
    2. 保存截图到 /app/alert_images/，生成 image_url
    3. 将 naive 时间字符串转换为带时区的 Aware Datetime
    4. 将 level 字符串映射为 AlertLevelEnum
    """
    camera_id: str = Field(description="摄像头唯一标识")
    message: str = Field(description="告警描述")
    level: AlertLevelEnum = Field(description="告警级别（网关层映射后的枚举）")
    confidence: float = Field(description="YOLO推理置信度", ge=0.0, le=1.0)
    timestamp: datetime = Field(description="告警抓拍时间（Aware Datetime，内部流转统一带时区）")
    detection_tags: Optional[str] = Field(default=None, description="检测标签扩展字段")
    image_url: Optional[str] = Field(default=None, description="告警截图相对路径，如 /alert_images/{uuid}.jpg")


class AlertPushResponse(ResponseBase):
    """告警推送响应模型

    约束：alert_id 必须放入 data 字段，保持统一响应结构，禁止在 data 同级扩展业务字段。
    正确示例：data={"alert_id": "ALT1745733600123A7F"}
    """


class AlertCoreModel(TraceBase):
    """告警数据核心存储模型，全项目唯一标准"""
    id: str = Field(description="告警唯一ID，固定格式ALT{timestamp}{random3}")
    camera_id: str = Field(description="摄像头唯一标识")
    camera_name: Optional[str] = Field(default=None, description="摄像头名称")
    store_id: Optional[str] = Field(
        default=None,
        description="摄像头所属门店唯一ID，与权限模型严格对齐，数据 Agent SQL 权限过滤直接基于该字段",
    )
    location: Optional[str] = Field(
        default=None,
        description="摄像头所属门店/区域中文位置（如 '南山店'），仅用于前端展示与告警话术，禁止用于权限过滤",
    )
    message: str = Field(description="告警描述")
    violation_type: ViolationTypeEnum = Field(description="违规类型编码")
    level: AlertLevelEnum = Field(description="告警级别")
    confidence: float = Field(description="YOLO推理置信度", ge=0.0, le=1.0)
    image_url: Optional[str] = Field(default=None, description="告警截图相对路径")
    detection_tags: Optional[str] = Field(default=None, description="检测标签扩展字段")
    bbox: Optional[List[List[float]]] = Field(
        default=None,
        description="YOLO 检测框坐标列表，二维数组以兼容多目标场景；每个元素为单个目标的 [x_min, y_min, x_max, y_max]，采用相对坐标 0.0-1.0",
    )
    is_read: bool = Field(default=False, description="告警是否已读")
    is_verified: bool = Field(default=False, description="是否经过VLM二次校验")
    verify_result: Optional[VerifyResultEnum] = Field(default=None, description="VLM二次校验结果枚举")
    rectification_status: RectificationStatusEnum = Field(
        default=RectificationStatusEnum.PENDING, description="整改状态枚举"
    )
    timestamp: datetime = Field(description="告警抓拍时间")
    created_at: datetime = Field(default_factory=beijing_now, description="告警数据入库时间（系统创建时间）")
    updated_at: datetime = Field(default_factory=beijing_now, description="数据更新时间")


class ViolationEventModel(TraceBase):
    """违规事件核心模型，监管研判 Agent（A组）VLM 二次校验后产出，全项目唯一标准。

    与 AlertCoreModel 的区别：
    - AlertCoreModel 记录原始边缘告警（输入），核心维度是 camera_id + timestamp；
    - ViolationEventModel 记录经 VLM 二次校验后的判定结果（输出），核心维度是 event_id；
    - 二者通过 alert_id 关联，但代表不同业务实体，禁止混淆。

    审计约束：所有 is_violation_confirmed=True 的事件必须完整填充
    event_id、verification_method、verified_at 字段，禁止缺失。
    """
    # 透传字段（保留原始告警信息，与 A 组输入字段一一对应）
    alert_id: str = Field(description="原始告警ID，与 AlertCoreModel.id 一致，关联溯源")
    camera_id: str = Field(description="摄像头唯一标识")
    camera_location: Optional[str] = Field(
        default=None,
        description="摄像头位置描述，如'一楼大厅'；语义等价于 AlertCoreModel.location",
    )
    store_id: Optional[str] = Field(
        default=None, description="摄像头所属门店唯一ID；网关层从 camera_id 映射补上，与 AlertCoreModel.store_id 对齐"
    )
    message: str = Field(description="告警描述")
    level: AlertLevelEnum = Field(description="告警级别，原始YOLO产出级别")
    confidence: float = Field(description="YOLO推理置信度", ge=0.0, le=1.0)
    image_url: Optional[str] = Field(
        default=None,
        description="原始告警图片URL；与 AlertCoreModel.image_url 对齐，原始告警无图时允许为 null",
    )
    detection_tags: Optional[str] = Field(default=None, description="检测标签扩展字段")
    is_read: bool = Field(default=False, description="已读状态")
    timestamp: datetime = Field(description="告警实际发生时间")
    created_at: datetime = Field(description="告警记录创建时间")

    # 研判产出字段（A组 VLM 二次校验结论）
    event_id: str = Field(
        description="判定生成的事件ID，Agent生成，全局唯一，后续整改/查询/台账的核心引用"
    )
    is_violation_confirmed: bool = Field(
        description="是否确认违规。True=确有违规，False=误报（误报也要落库，审计要求）"
    )
    severity_level: Optional[SeverityLevelEnum] = Field(
        default=None,
        description="违规严重等级，仅确认违规时填写，误报时为null",
    )
    verified_image_url: str = Field(
        description="本次校验所用的图片URL（去重后选中的那张），审计留痕'判定依据的是哪张图'"
    )
    regulation_clause: Optional[str] = Field(
        default=None,
        description="关联的法规条款，如'GB 31654-2021 第8.2.3条'，需RAG匹配，当前阶段可选",
    )
    verification_method: VerificationMethodEnum = Field(
        description="校验方式，vlm=云端VLM，edge_rule=降级为边缘规则，下游需区分结论可信度"
    )
    vlm_confidence: Optional[float] = Field(
        default=None, description="VLM判定置信度(0~1)，降级模式时为null", ge=0.0, le=1.0
    )
    model_version: Optional[str] = Field(
        default=None, description="VLM模型版本号，审计可追溯性强制要求"
    )
    verified_at: datetime = Field(description="校验完成时间，审计可追溯性强制要求")
    determination_basis: Optional[str] = Field(
        default=None, description="判定依据文字说明，审计可追溯性强制要求"
    )
    aggregation_count: int = Field(
        default=1,
        description="聚合的原始告警数量，1=单条直传，>1=聚合（如10分钟10条同类告警聚合为1条事件）",
        ge=1,
    )
    updated_at: datetime = Field(default_factory=beijing_now, description="数据更新时间")


class AlertDetailResponse(ResponseBase):
    """告警详情查询响应模型，路由/监管/数据Agent通用"""
    alert_detail: AlertCoreModel = Field(description="告警详情")


class AlertListQueryRequest(RequestBase):
    """告警列表查询请求模型"""
    time_range: Optional[Tuple[datetime, datetime]] = Field(default=None, description="查询时间范围")
    store_scope: Optional[List[str]] = Field(default=None, description="门店范围过滤")
    violation_type: Optional[List[ViolationTypeEnum]] = Field(default=None, description="违规类型过滤")
    risk_level: Optional[List[AlertLevelEnum]] = Field(default=None, description="告警级别过滤")
    rectification_status: Optional[List[RectificationStatusEnum]] = Field(
        default=None, description="整改状态过滤"
    )
    page_num: int = Field(default=1, description="页码", ge=1)
    page_size: int = Field(default=20, description="每页条数", ge=1, le=100)


class AlertListQueryResponse(PageResponseBase):
    """告警列表查询响应模型，继承全项目通用分页基类。"""
    items: List[AlertCoreModel] = Field(description="当前页的告警列表数据")


class AlertWebSocketMessage(BaseModel):
    """WebSocket 实时告警推送消息模型"""
    entity: str = Field(default="alert", description="实体类型：alert")
    action: str = Field(description="操作类型：create/update/delete")
    payload: AlertCoreModel = Field(description="告警数据载荷")


class AlertMQTTMessage(BaseModel):
    """MQTT 告警推送消息模型，对接第三方平台"""
    operator: str = Field(default="RecordPush", description="操作标识")
    info: Dict[str, Any] = Field(description="推送详情，包含 RecordID、aibox_id、alarm_txt、time、pic 等字段")


class EventDetailResponse(ResponseBase):
    """违规事件详情查询响应模型，路由/监管/数据Agent通用"""
    event_detail: ViolationEventModel = Field(description="违规事件详情，含 VLM 二次校验完整结论")


class EventListQueryResponse(PageResponseBase):
    """违规事件列表查询响应模型，继承全项目通用分页基类。"""
    items: List[ViolationEventModel] = Field(description="当前页的违规事件列表数据")


# ---------------------------------------------------------------------------
# 用户与权限核心模型
# ---------------------------------------------------------------------------

class UserInfoModel(TraceBase):
    """用户信息核心模型，全项目通用"""
    user_id: str = Field(description="用户唯一ID")
    user_name: str = Field(description="用户姓名")
    role_type: UserRoleEnum = Field(description="用户角色")
    phone: Optional[str] = Field(default=None, description="联系电话")
    email: Optional[str] = Field(default=None, description="邮箱")
    store_ids: List[str] = Field(default_factory=list, description="有权限访问的门店ID列表")
    region_ids: List[str] = Field(default_factory=list, description="有权限访问的区域ID列表")
    permission_actions: List[PermissionActionEnum] = Field(default_factory=list, description="可执行的操作权限枚举列表，详见 PermissionActionEnum")
    created_at: datetime = Field(default_factory=beijing_now, description="账号创建时间")
    last_login_time: Optional[datetime] = Field(default=None, description="最后登录时间")


class PermissionContext(TraceBase):
    """权限上下文模型，全链路透传，用于数据隔离与权限校验"""
    user_id: str = Field(description="操作用户ID")
    role_type: UserRoleEnum = Field(description="用户角色")
    store_scope: List[str] = Field(default_factory=list, description="可访问的门店范围")
    region_scope: List[str] = Field(default_factory=list, description="可访问的区域范围")
    permission_actions: List[str] = Field(default_factory=list, description="可执行的操作权限")


class SessionContext(TraceBase):
    """会话上下文模型，路由Agent多轮对话专用。

    约束：chat_history 最大保留轮次不得超过 10 轮，超出时由服务端在组装 Prompt 前进行滑动窗口截断。
    """
    session_id: str = Field(description="会话唯一ID")
    user_id: str = Field(description="所属用户ID")
    last_intent: Optional[UserIntentEnum] = Field(default=None, description="上一轮用户意图")
    last_slots: Optional[Dict[str, Any]] = Field(default=None, description="上一轮已填充的槽位信息")
    last_result_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="上一轮查询结果快照")
    pending_confirmation_id: Optional[str] = Field(default=None, description="待确认的操作ID")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="对话历史列表，最大保留10轮，由 ChatMessage 强类型约束")
    created_at: datetime = Field(default_factory=beijing_now, description="会话创建时间")
    updated_at: datetime = Field(default_factory=beijing_now, description="会话更新时间")
    expire_time: datetime = Field(
        default_factory=lambda: beijing_now() + timedelta(minutes=30),
        description="会话过期时间，默认30分钟",
    )


# ---------------------------------------------------------------------------
# Agent通信与路由核心模型
# ---------------------------------------------------------------------------

class AgentEventModel(TraceBase):
    """Agent间通信事件标准模型，基建组消息总线通用。"""
    event_id: str = Field(description="事件唯一ID")
    event_type: AgentEventTypeEnum = Field(
        description="事件类型，必须为 AgentEventTypeEnum 注册枚举值"
    )
    source_agent: str = Field(description="事件来源Agent：router_agent/triage_agent/data_agent/infra")
    target_agent: Optional[str] = Field(default=None, description="目标Agent，为空则广播")
    payload: Dict[str, Any] = Field(description="事件业务数据，遵循对应场景Schema")
    timestamp: datetime = Field(default_factory=beijing_now, description="事件触发时间")
    priority: int = Field(default=1, description="事件优先级，1-5，1最高")


class IntentRecognitionResult(TraceBase):
    """意图识别结果模型，路由Agent核心输出"""
    user_query: str = Field(description="用户原始提问")
    intent_type: UserIntentEnum = Field(description="识别出的用户意图")
    intent_confidence: float = Field(description="意图识别置信度", ge=0.0, le=1.0)
    slots: Dict[str, Any] = Field(default_factory=dict, description="已提取的槽位信息")
    missing_slots: List[str] = Field(default_factory=list, description="缺失的必填槽位")
    target_agent: str = Field(description="目标处理Agent")
    target_tool: Optional[str] = Field(default=None, description="目标调用工具名称")
    tool_args: Optional[Dict[str, Any]] = Field(default=None, description="工具调用入参")
    need_clarification: bool = Field(default=False, description="是否需要向用户澄清")
    clarification_content: Optional[str] = Field(default=None, description="澄清话术")
    is_out_of_domain: bool = Field(default=False, description="是否为领域外问题")


class RoutePlanModel(TraceBase):
    """路由执行计划模型，复杂任务编排专用"""
    plan_id: str = Field(description="执行计划唯一ID")
    session_id: str = Field(description="所属会话ID")
    user_id: str = Field(description="操作用户ID")
    intent_type: UserIntentEnum = Field(description="用户意图")
    step_order: List[Dict[str, Any]] = Field(
        description="执行步骤顺序，每个元素包含 agent、tool、args、depends_on 字段"
    )
    current_step: int = Field(default=1, description="当前执行步骤")
    execution_status: ExecutionStatusEnum = Field(
        default=ExecutionStatusEnum.PLANNED,
        description="执行状态枚举，详见 ExecutionStatusEnum",
    )
    error_code: Optional[str] = Field(default=None, description="执行失败错误码")
    error_message: Optional[str] = Field(default=None, description="执行失败描述")
    retry_count: int = Field(default=0, description="已重试次数")
    max_retry: int = Field(default=3, description="最大重试次数")
    created_at: datetime = Field(default_factory=beijing_now, description="计划创建时间")
    updated_at: datetime = Field(default_factory=beijing_now, description="计划更新时间")


class ConfirmationModel(TraceBase):
    """高危操作二次确认模型，路由Agent专用"""
    confirmation_id: str = Field(description="确认单唯一ID")
    session_id: str = Field(description="所属会话ID")
    user_id: str = Field(description="操作用户ID")
    action_type: ActionTypeEnum = Field(description="操作类型枚举，详见 ActionTypeEnum")
    action_preview: str = Field(description="操作预览描述，展示给用户确认")
    action_params: Dict[str, Any] = Field(description="操作执行入参")
    confirmation_status: str = Field(
        default="pending",
        description="确认状态：pending/confirmed/rejected/expired",
    )
    created_at: datetime = Field(default_factory=beijing_now, description="创建时间")
    expires_at: datetime = Field(
        default_factory=lambda: beijing_now() + timedelta(minutes=15),
        description="过期时间，默认15分钟",
    )


class ChatMessageRequest(RequestBase):
    """前端→路由Agent聊天消息请求模型"""
    session_id: str = Field(description="会话ID")
    message_text: str = Field(description="用户输入文本内容")
    input_type: str = Field(default="text", description="输入类型：text/button/file/confirmation")
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None, description="附件列表")
    confirmation_id: Optional[str] = Field(default=None, description="确认/取消操作对应的确认单ID")


class ChatMessageResponse(ResponseBase):
    """路由Agent→前端聊天消息响应模型"""
    session_id: str = Field(description="会话ID")
    response_type: str = Field(
        description="响应类型：answer/clarification/confirmation_preview/refusal/error/guidance",
    )
    answer_payload: str = Field(description="响应文本内容")
    structured_summary: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default=None, description="结构化数据，用于前端卡片/图表渲染"
    )
    guidance_type: str = Field(default="none", description="引导类型：none/followup_query/rectification/export/notify")
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list, description="建议操作按钮列表")
    pending_confirmation: Optional[ConfirmationModel] = Field(default=None, description="待确认操作信息")


# ---------------------------------------------------------------------------
# 数据Agent专用模型
# ---------------------------------------------------------------------------

class FoodSafetyDataQueryRequest(RequestBase):
    """路由Agent→数据Agent统一查询请求模型，Function Calling专用。

    实例化约束：
    1. 调用方既可显式传入 user_id，也可仅传 permission_context，由前置验证器自动从
       permission_context.user_id 回填基类的 user_id；
    2. 若两者同时传入但取值不一致，校验失败并抛出 ValueError；
    3. trace_id、request_time 由 TraceBase / RequestBase 的 default_factory 自动生成。
    """
    user_query: str = Field(description="用户自然语言查询问题")
    scene: QuerySceneEnum = Field(default=QuerySceneEnum.ALARM_QUERY, description="查询场景枚举，详见 QuerySceneEnum")
    time_range: Optional[Tuple[datetime, datetime]] = Field(default=None, description="时间范围槽位")
    store_scope: Optional[List[str]] = Field(default=None, description="门店范围槽位")
    region_scope: Optional[List[str]] = Field(default=None, description="区域范围槽位")
    violation_type: Optional[List[ViolationTypeEnum]] = Field(default=None, description="违规类型槽位")
    risk_level: Optional[List[AlertLevelEnum]] = Field(default=None, description="风险等级槽位")
    event_id: Optional[str] = Field(
        default=None,
        description="告警 ID（AlertCoreModel.id）或事件 ID（ViolationEventModel.event_id）槽位",
    )
    task_id: Optional[str] = Field(default=None, description="整改工单ID槽位")
    chat_history: Optional[List[ChatMessage]] = Field(default=None, description="对话历史，用于多轮指代消解，由 ChatMessage 强类型约束")
    permission_context: PermissionContext = Field(description="权限上下文，用于数据隔离")

    @model_validator(mode="before")
    @classmethod
    def _auto_fill_user_id(cls, data: Any) -> Any:
        """前置：未显式传 user_id 但已传 permission_context 时，自动回填。"""
        if isinstance(data, dict) and not data.get("user_id"):
            ctx = data.get("permission_context")
            ctx_user_id = (
                ctx.get("user_id") if isinstance(ctx, dict) else getattr(ctx, "user_id", None)
            )
            if ctx_user_id:
                data["user_id"] = ctx_user_id
        return data

    @model_validator(mode="after")
    def _ensure_user_id_match_context(self) -> "FoodSafetyDataQueryRequest":
        """后置：强制 user_id 与 permission_context.user_id 一致，杜绝越权。"""
        if self.user_id != self.permission_context.user_id:
            raise ValueError(
                f"user_id ({self.user_id!r}) 必须与 permission_context.user_id "
                f"({self.permission_context.user_id!r}) 严格一致"
            )
        return self


class SQLGenerateResult(TraceBase):
    """SQL生成结果模型，数据Agent内部流转专用"""
    user_query: str = Field(description="用户原始查询")
    generated_sql: str = Field(description="生成的纯净SQL语句")
    sql_generation_status: SqlGenerationStatusEnum = Field(description="SQL 生成状态枚举")
    error_message: Optional[str] = Field(default=None, description="错误描述")
    retry_count: int = Field(default=0, description="已重试次数")


class ASTSecurityCheckResult(TraceBase):
    """AST安全校验结果模型，数据Agent/基建拦截器通用"""
    original_sql: str = Field(description="原始SQL语句")
    is_pass: bool = Field(description="是否校验通过")
    blocked_type: Optional[BlockedTypeEnum] = Field(
        default=None,
        description="拦截类型枚举，详见 BlockedTypeEnum",
    )
    reason: str = Field(description="校验结果描述/拦截原因")


class ASTPerformanceCheckResult(TraceBase):
    """AST性能校验结果模型，数据Agent/基建拦截器通用"""
    original_sql: str = Field(description="原始SQL语句")
    is_pass: bool = Field(description="是否校验通过")
    is_modified: bool = Field(description="是否自动修正SQL")
    processed_sql: str = Field(description="处理后的SQL语句")
    auto_limit_value: Optional[int] = Field(default=None, description="自动追加的LIMIT值")
    reason: str = Field(description="校验结果描述/拦截原因")


class DBExecuteResult(TraceBase):
    """数据库执行结果模型，数据Agent专用"""
    execute_sql: str = Field(description="最终执行的SQL语句")
    db_result_data: List[Dict[str, Any]] = Field(default_factory=list, description="查询结果数据集")
    db_result_rows: int = Field(description="查询结果行数")
    db_execute_status: DbExecuteStatusEnum = Field(description="数据库执行状态枚举")
    db_execution_latency_ms: int = Field(description="SQL执行耗时，单位毫秒")
    error_message: Optional[str] = Field(default=None, description="错误描述")


class DataAgentResponse(ResponseBase):
    """数据Agent→路由Agent统一响应模型。

    消费契约（强约束）：
    1. 调用方在读取业务字段前，必须先校验基类 success=True 且 code=='0000'，二者缺一不可；
    2. 失败场景下，translated_text 与 structured_summary 必须为 None，错误详情统一走基类字段；
    3. 严禁仅以 translated_text 是否非空作为成功判断依据。
    """
    translated_text: Optional[str] = Field(
        default=None,
        description="自然语言翻译后的查询结果，仅在 success=True 且 code='0000' 时填充",
    )
    structured_summary: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default=None,
        description="结构化数据摘要，与 translated_text 同步填充/置空",
    )
    original_sql: Optional[str] = Field(default=None, description="执行的原始SQL，仅审计用")
    execute_latency_ms: Optional[int] = Field(default=None, description="执行总耗时")

    @model_validator(mode="after")
    def _ensure_payload_match_status(self) -> "DataAgentResponse":
        """成功响应必须有业务结果；失败响应必须置空业务字段。"""
        is_success = self.success and self.code == "0000"
        if is_success:
            if self.translated_text is None:
                raise ValueError("成功响应（success=True 且 code='0000'）必须填充 translated_text")
        else:
            if self.translated_text is not None or self.structured_summary is not None:
                raise ValueError(
                    "失败响应禁止填充 translated_text/structured_summary，错误详情请走 message/code/data"
                )
        return self


# ---------------------------------------------------------------------------
# 审计日志核心模型
# ---------------------------------------------------------------------------

class AuditLogModel(TraceBase):
    """全局审计日志核心模型，全项目通用。

    脱敏强约束：input_data、output_data 落库前必须经 src/core/logger.py 提供的统一脱敏工具处理，
    禁止明文写入敏感字段。
    """
    audit_id: str = Field(description="审计日志唯一ID")
    event_type: AuditEventTypeEnum = Field(description="审计事件类型")
    operator: str = Field(description="操作主体：user_id/系统/agent名称")
    action: str = Field(description="操作描述")
    input_data: Optional[str] = Field(default=None, description="操作入参（已脱敏）的 JSON 字符串")
    output_data: Optional[str] = Field(default=None, description="操作出参（已脱敏）的 JSON 字符串")
    success: bool = Field(description="操作是否成功")
    error_code: Optional[str] = Field(default=None, description="操作失败错误码")
    error_message: Optional[str] = Field(default=None, description="操作失败描述")
    latency_ms: Optional[int] = Field(default=None, description="操作耗时，单位毫秒")
    user_id: Optional[str] = Field(default=None, description="关联操作用户ID")
    session_id: Optional[str] = Field(default=None, description="关联会话ID")
    alert_id: Optional[str] = Field(default=None, description="关联告警ID")
    event_time: datetime = Field(default_factory=beijing_now, description="事件发生时间（带北京时区）")


# ---------------------------------------------------------------------------
# __all__ 导出声明
# ---------------------------------------------------------------------------

__all__ = [
    # 工具函数
    "BEIJING_TZ",
    "beijing_now",
    # 枚举
    "UserRoleEnum",
    "AlertLevelEnum",
    "VerifyResultEnum",
    "ViolationTypeEnum",
    "UserIntentEnum",
    "RectificationStatusEnum",
    "SeverityLevelEnum",
    "VerificationMethodEnum",
    "AgentEventTypeEnum",
    "SqlGenerationStatusEnum",
    "DbExecuteStatusEnum",
    "AuditEventTypeEnum",
    "ExecutionStatusEnum",
    "ActionTypeEnum",
    "BlockedTypeEnum",
    "QuerySceneEnum",
    "PermissionActionEnum",
    # 基类
    "TraceBase",
    "RequestBase",
    "ResponseBase",
    "PageResponseBase",
    "ChatMessage",
    # 告警模型
    "EdgeAlertPayload",
    "AlertPushRequest",
    "AlertPushResponse",
    "AlertCoreModel",
    "ViolationEventModel",
    "AlertDetailResponse",
    "AlertListQueryRequest",
    "AlertListQueryResponse",
    "AlertWebSocketMessage",
    "AlertMQTTMessage",
    "EventDetailResponse",
    "EventListQueryResponse",
    # 用户与权限
    "UserInfoModel",
    "PermissionContext",
    "SessionContext",
    # Agent通信与路由
    "AgentEventModel",
    "IntentRecognitionResult",
    "RoutePlanModel",
    "ConfirmationModel",
    "ChatMessageRequest",
    "ChatMessageResponse",
    # 数据Agent
    "FoodSafetyDataQueryRequest",
    "SQLGenerateResult",
    "ASTSecurityCheckResult",
    "ASTPerformanceCheckResult",
    "DBExecuteResult",
    "DataAgentResponse",
    # 审计日志
    "AuditLogModel",
]
