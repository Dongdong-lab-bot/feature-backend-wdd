"""
全局异常体系模块 (exceptions.py)

定义项目统一的异常基类，按场景拆分异常类型，实现标准化错误码、异常信息。
全项目所有异常必须继承 ProjectBaseException 基类，禁止裸抛 Python 原生 Exception。
"""

from enum import Enum


class ErrorCodeEnum(Enum):
    """全局错误码枚举

    编码规则：
    - 0000：成功
    - 1xxx：通用参数/配置异常
    - 2xxx：大模型相关异常
    - 3xxx：数据安全/权限相关异常
    - 4xxx：数据库/存储相关异常
    - 5xxx：Agent业务相关异常
    """
    SUCCESS = "0000"

    # 通用异常
    PARAM_ERROR = "1001"
    CONFIG_ERROR = "1002"

    # 大模型异常
    LLM_CALL_FAILED = "2001"
    LLM_RESPONSE_INVALID = "2002"
    LLM_FUSE_TRIGGERED = "2003"

    # 安全异常
    SQL_SECURITY_BLOCKED = "3001"
    SQL_PERFORMANCE_BLOCKED = "3002"
    PERMISSION_DENIED = "3003"

    # 数据库异常
    DB_CONNECT_FAILED = "4001"
    DB_EXECUTE_FAILED = "4002"
    DB_RESULT_EMPTY = "4003"

    # Agent业务异常
    AGENT_INIT_FAILED = "5001"
    AGENT_HANDLE_FAILED = "5002"
    ROUTE_FAILED = "5003"

    # 路由Agent异常
    INTENT_RECOGNITION_FAILED = "6001"
    ROUTE_DISPATCH_FAILED = "6002"
    CONFIRMATION_EXPIRED = "6003"

    # 监管研判 Agent 异常
    ALERT_PUSH_FAILED = "7001"          # Deprecated: 改用 8002
    ALERT_DUPLICATE = "7002"
    VLM_VERIFY_FAILED = "7003"

    # 核心基建组异常
    GATEWAY_REQUEST_INVALID = "8001"
    EDGE_ALERT_PUSH_FAILED = "8002"
    STORAGE_FAILED = "8003"


class ProjectBaseException(Exception):
    """项目全局异常基类

    所有业务异常必须继承此类，禁止直接使用 Python 原生 Exception。
    """

    def __init__(
        self,
        error_code: ErrorCodeEnum,
        message: str,
        detail: dict = None
    ):
        self.error_code = error_code
        self.message = message
        self.detail = detail or {}
        super().__init__(f"[{error_code.value}] {message}")

    def to_dict(self) -> dict:
        """转换为字典，用于接口返回"""
        return {
            "code": self.error_code.value,
            "message": self.message,
            "detail": self.detail,
            "success": False
        }


# 通用参数异常
class ParamError(ProjectBaseException):
    def __init__(self, message: str = "参数错误", detail: dict = None):
        super().__init__(ErrorCodeEnum.PARAM_ERROR, message, detail)


class ConfigError(ProjectBaseException):
    def __init__(self, message: str = "配置错误", detail: dict = None):
        super().__init__(ErrorCodeEnum.CONFIG_ERROR, message, detail)


# 大模型调用异常
class LLMCallFailedError(ProjectBaseException):
    def __init__(self, message: str = "大模型调用失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.LLM_CALL_FAILED, message, detail)


class LLMResponseInvalidError(ProjectBaseException):
    def __init__(self, message: str = "大模型响应格式无效", detail: dict = None):
        super().__init__(ErrorCodeEnum.LLM_RESPONSE_INVALID, message, detail)


class LLMFuseTriggeredError(ProjectBaseException):
    def __init__(self, message: str = "大模型熔断已触发", detail: dict = None):
        super().__init__(ErrorCodeEnum.LLM_FUSE_TRIGGERED, message, detail)


# SQL安全拦截异常
class SQLSecurityBlockedError(ProjectBaseException):
    def __init__(self, message: str = "SQL安全校验不通过，已拦截", detail: dict = None):
        super().__init__(ErrorCodeEnum.SQL_SECURITY_BLOCKED, message, detail)


class SQLPerformanceBlockedError(ProjectBaseException):
    def __init__(self, message: str = "SQL性能校验不通过，已拦截", detail: dict = None):
        super().__init__(ErrorCodeEnum.SQL_PERFORMANCE_BLOCKED, message, detail)


# 权限拒绝异常
class PermissionDeniedError(ProjectBaseException):
    def __init__(self, message: str = "权限不足，操作被拒绝", detail: dict = None):
        super().__init__(ErrorCodeEnum.PERMISSION_DENIED, message, detail)


# 数据库执行异常
class DBConnectFailedError(ProjectBaseException):
    def __init__(self, message: str = "数据库连接失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.DB_CONNECT_FAILED, message, detail)


class DBExecuteFailedError(ProjectBaseException):
    def __init__(self, message: str = "数据库执行失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.DB_EXECUTE_FAILED, message, detail)


class DBResultEmptyError(ProjectBaseException):
    def __init__(self, message: str = "查询结果为空", detail: dict = None):
        super().__init__(ErrorCodeEnum.DB_RESULT_EMPTY, message, detail)


# Agent业务异常
class AgentInitFailedError(ProjectBaseException):
    def __init__(self, message: str = "Agent初始化失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.AGENT_INIT_FAILED, message, detail)


class AgentHandleFailedError(ProjectBaseException):
    def __init__(self, message: str = "Agent处理失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.AGENT_HANDLE_FAILED, message, detail)


class RouteFailedError(ProjectBaseException):
    def __init__(self, message: str = "路由失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.ROUTE_FAILED, message, detail)


class IntentRecognitionFailedError(ProjectBaseException):
    def __init__(self, message: str = "用户意图识别失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.INTENT_RECOGNITION_FAILED, message, detail)


class RouteDispatchFailedError(ProjectBaseException):
    def __init__(self, message: str = "Agent路由分发失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.ROUTE_DISPATCH_FAILED, message, detail)


class ConfirmationExpiredError(ProjectBaseException):
    def __init__(self, message: str = "高危操作二次确认单已过期", detail: dict = None):
        super().__init__(ErrorCodeEnum.CONFIRMATION_EXPIRED, message, detail)


class AlertPushFailedError(ProjectBaseException):
    def __init__(self, message: str = "边缘告警数据推送失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.ALERT_PUSH_FAILED, message, detail)


class AlertDuplicateError(ProjectBaseException):
    def __init__(self, message: str = "告警数据重复", detail: dict = None):
        super().__init__(ErrorCodeEnum.ALERT_DUPLICATE, message, detail)


class VLMVerifyFailedError(ProjectBaseException):
    def __init__(self, message: str = "VLM二次校验调用失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.VLM_VERIFY_FAILED, message, detail)


class GatewayRequestInvalidError(ProjectBaseException):
    def __init__(self, message: str = "网关请求解析失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.GATEWAY_REQUEST_INVALID, message, detail)


class EdgeAlertPushFailedError(ProjectBaseException):
    def __init__(self, message: str = "边缘告警数据推送失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.EDGE_ALERT_PUSH_FAILED, message, detail)


class StorageFailedError(ProjectBaseException):
    def __init__(self, message: str = "存储写入失败", detail: dict = None):
        super().__init__(ErrorCodeEnum.STORAGE_FAILED, message, detail)


__all__ = [
    "ErrorCodeEnum",
    "ProjectBaseException",
    "ParamError",
    "ConfigError",
    "LLMCallFailedError",
    "LLMResponseInvalidError",
    "LLMFuseTriggeredError",
    "SQLSecurityBlockedError",
    "SQLPerformanceBlockedError",
    "PermissionDeniedError",
    "DBConnectFailedError",
    "DBExecuteFailedError",
    "DBResultEmptyError",
    "AgentInitFailedError",
    "AgentHandleFailedError",
    "RouteFailedError",
    "IntentRecognitionFailedError",
    "RouteDispatchFailedError",
    "ConfirmationExpiredError",
    "AlertPushFailedError",
    "AlertDuplicateError",
    "VLMVerifyFailedError",
    "GatewayRequestInvalidError",
    "EdgeAlertPushFailedError",
    "StorageFailedError",
]
