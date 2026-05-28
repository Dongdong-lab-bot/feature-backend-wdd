"""
结构化日志工具类 (logger.py)

基于 loguru 开发，实现全链路 trace_id 关联、审计日志、日志分级存储。
严格对齐可追溯红线要求，禁止关闭核心操作日志，禁止敏感信息明文打印。
"""

import os
import sys
from contextvars import ContextVar
from loguru import logger
from typing import Optional, Any
from uuid import uuid4

# 延迟导入避免循环依赖
_project_settings = None


def _get_project_settings():
    """懒加载项目配置，避免循环导入"""
    global _project_settings
    if _project_settings is None:
        from .config import project_settings as ps
        _project_settings = ps
    return _project_settings


# 敏感信息字段列表，日志中遇到这些字段会进行脱敏
SENSITIVE_FIELDS = ["password", "api_key", "secret", "token", "key", "passwd", "pwd"]


def mask_sensitive_data(data: dict) -> dict:
    """敏感信息脱敏

    遍历字典，对敏感字段的值进行掩码处理，避免密码、密钥等信息泄露到日志中。
    """
    if not isinstance(data, dict):
        return data
    masked_data = {}
    for k, v in data.items():
        # 检查键名是否包含敏感关键词（不区分大小写）
        if any(field in k.lower() for field in SENSITIVE_FIELDS):
            masked_data[k] = "******"
        elif isinstance(v, dict):
            masked_data[k] = mask_sensitive_data(v)
        elif isinstance(v, list):
            masked_data[k] = [
                mask_sensitive_data(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            masked_data[k] = v
    return masked_data


# 移除 loguru 默认处理器
logger.remove()

# 控制台输出格式（开发环境，带颜色）
_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
    "<magenta>trace_id={extra[trace_id]}</magenta> | "
    "<level>{message}</level>"
)

# 文件输出格式（所有环境，无颜色标记）
_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} | "
    "trace_id={extra[trace_id]} | {message}"
)

# 新增 AUDIT 审计日志级别（no=25，介于 INFO(20) 和 WARNING(30) 之间）
logger.level("AUDIT", no=25, color="<blue>")


def _setup_handlers() -> None:
    """根据项目配置设置日志处理器"""
    ps = _get_project_settings()
    debug_mode = ps.debug
    os.makedirs("logs", exist_ok=True)

    def _safe_add(sink: Any, **kwargs: Any) -> None:
        try:
            logger.add(sink, **kwargs)
        except PermissionError:
            fallback_kwargs = dict(kwargs)
            fallback_kwargs["enqueue"] = False
            logger.add(sink, **fallback_kwargs)

    # 控制台处理器（开发环境输出）
    # debug 模式下审计日志也输出到控制台，方便开发调试
    _safe_add(
        sys.stdout,
        format=_CONSOLE_FORMAT,
        level="DEBUG" if debug_mode else "INFO",
        enqueue=True,
        backtrace=True,
        diagnose=debug_mode,
        filter=lambda record: (
            record["level"].name != "AUDIT" or debug_mode
        ),
    )

    # 普通运行日志文件
    _safe_add(
        "logs/runtime_{time:YYYY-MM-DD}.log",
        format=_FILE_FORMAT,
        level="INFO",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    # 审计日志文件（核心红线：所有操作留痕，永久留存 365 天）
    _safe_add(
        "logs/audit_{time:YYYY-MM-DD}.log",
        format=_FILE_FORMAT,
        level="AUDIT",
        rotation="00:00",
        retention="365 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    # 错误日志文件
    _safe_add(
        "logs/error_{time:YYYY-MM-DD}.log",
        format=_FILE_FORMAT,
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )


# 初始化日志处理器
_setup_handlers()


# contextvars.ContextVar 支持多线程/异步并发场景下的 trace_id 隔离
_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class TraceContext:
    """全局 trace_id 上下文管理

    基于 contextvars.ContextVar 实现，支持多线程和异步并发环境下的
    trace_id 隔离，确保单次请求/告警处理全链路共用一个 trace_id。
    """

    @classmethod
    def get_trace_id(cls) -> str:
        tid = _trace_id_var.get()
        if tid is None:
            tid = uuid4().hex
            _trace_id_var.set(tid)
        return tid

    @classmethod
    def set_trace_id(cls, trace_id: str) -> None:
        _trace_id_var.set(trace_id)

    @classmethod
    def clear_trace_id(cls) -> None:
        _trace_id_var.set(None)


class BoundLogger:
    """绑定 trace_id 的日志包装器

    所有日志输出自动携带当前上下文中的 trace_id，实现全链路追踪。
    审计日志必须通过 audit() 方法记录，确保核心操作留痕。
    """

    def __init__(self):
        self._logger = logger

    def _get_logger(self):
        return self._logger.bind(trace_id=TraceContext.get_trace_id())

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._get_logger().debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._get_logger().info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._get_logger().warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._get_logger().error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._get_logger().critical(message, *args, **kwargs)

    def audit(self, message: str, *args: Any, **kwargs: Any) -> None:
        """审计日志专用方法，核心操作必须调用此方法留痕

        强制埋点场景包括但不限于：
        - 所有大模型调用（入参、出参、耗时、状态）
        - 所有 SQL 执行操作（SQL 语句、执行结果、耗时）
        - 所有用户操作、权限校验
        - 所有 Agent 生命周期管理、消息收发
        - 所有异常拦截、熔断降级触发
        """
        self._get_logger().log("AUDIT", message, *args, **kwargs)

    def bind(self, **kwargs: Any):
        """创建带有额外上下文的子日志器"""
        return self._get_logger().bind(**kwargs)


# 全局日志实例，全项目直接导入使用
log = BoundLogger()

__all__ = [
    "log",
    "TraceContext",
    "mask_sensitive_data",
    "SENSITIVE_FIELDS",
]
