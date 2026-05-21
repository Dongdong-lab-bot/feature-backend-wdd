"""
Agent 抽象基类 (base_agent.py)

定义标准生命周期方法，内置熔断降级、日志埋点、异常处理通用逻辑。
所有业务 Agent 必须继承此类，通过元类自动注册到 AgentRegistry。

设计对齐：
- 生命周期：__init__ → run → handle_event → stop
- 熔断器：CLOSED(正常) → OPEN(熔断) → HALF_OPEN(试探) → CLOSED(恢复)
- 日志：所有关键操作自动调用 log.audit() 埋点
- 异常：统一转换为 ProjectBaseException，禁止裸抛 Exception
"""

from __future__ import annotations

import asyncio
import time
import traceback
import uuid
from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from src.core.logger import log, TraceContext
from src.core.exceptions import (
    AgentHandleFailedError,
    AgentInitFailedError,
    ProjectBaseException,
)
from src.core.config import redis_settings
from src.core.message_bus import MessageBus, MessageBusFactory
from src.core.schemas import AgentEventModel, AgentEventTypeEnum
from src.core.circuit_breaker import CircuitBreaker, FuseState


# ---------------------------------------------------------------------------
# 状态与熔断枚举
# ---------------------------------------------------------------------------

class AgentStatus(str, Enum):
    """Agent 运行状态枚举"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    BUSY = "busy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Agent 注册表
# ---------------------------------------------------------------------------

class AgentRegistry:
    """Agent 插件注册表

    维护所有已注册的 Agent 子类，支持按名称查找。
    子类继承 BaseAgent 时通过元类自动注册，无需手动调用。
    """

    _agents: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
        """注册 Agent 子类

        Raises:
            ValueError: 类名重复时抛出，禁止覆盖已有注册
        """
        name = agent_class.__name__
        if name in cls._agents:
            raise ValueError(
                f"Agent class name conflict: '{name}' is already registered "
                f"by {cls._agents[name].__module__}."
            )
        cls._agents[name] = agent_class
        return agent_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseAgent]]:
        """按名称获取已注册的 Agent 类"""
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> Dict[str, Type[BaseAgent]]:
        """获取所有已注册的 Agent"""
        return cls._agents.copy()

    @classmethod
    def clear(cls) -> None:
        """清空注册表（仅测试使用）"""
        cls._agents.clear()


# ---------------------------------------------------------------------------
# Agent 元类：自动注册
# ---------------------------------------------------------------------------

class BaseAgentMeta(ABCMeta):
    """Agent 元类：自动将非抽象子类注册到 AgentRegistry"""

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)
        # 排除 BaseAgent 本身及抽象中间类
        if (
            name != "BaseAgent"
            and not getattr(cls, "__abstractmethods__", False)
            and any(getattr(b, "_is_base_agent", False) for b in bases)
        ):
            AgentRegistry.register(cls)
            log.info(f"Agent auto-registered: {name}")
        return cls


# ---------------------------------------------------------------------------
# Agent 抽象基类
# ---------------------------------------------------------------------------

class BaseAgent(ABC, metaclass=BaseAgentMeta):
    """Agent 抽象基类

    生命周期：
        __init__ → run() → [handle_event() …] → stop()

    子类必须实现：
        - run()       : Agent 启动逻辑
        - _on_event() : 具体的事件处理逻辑

    子类可覆盖：
        - FUSE_FAILURE_THRESHOLD   : 熔断触发阈值（默认 5 次）
        - FUSE_RECOVERY_TIMEOUT    : 熔断恢复超时（默认 60 秒）
        - FUSE_HALF_OPEN_MAX_CALLS : 半开状态最大试探次数（默认 3 次）
    """

    _is_base_agent = True  # 用于元类识别

    # ---- 熔断默认配置（子类可覆盖） ----
    # 单位与取值范围约束：
    #   FUSE_FAILURE_THRESHOLD   — 次，≥1，默认 5
    #   FUSE_RECOVERY_TIMEOUT    — 秒，≥10，默认 60.0
    #   FUSE_HALF_OPEN_MAX_CALLS — 次，≥1，默认 3
    FUSE_FAILURE_THRESHOLD: int = 5
    FUSE_RECOVERY_TIMEOUT: float = 60.0
    FUSE_HALF_OPEN_MAX_CALLS: int = 3

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.config = config or {}
        self._status = AgentStatus.INITIALIZING

        # 熔断器：复用独立的 CircuitBreaker 组件
        self._fuse = CircuitBreaker(
            name=f"agent:{self.agent_name}",
            failure_threshold=self.FUSE_FAILURE_THRESHOLD,
            recovery_timeout=self.FUSE_RECOVERY_TIMEOUT,
            half_open_max_calls=self.FUSE_HALF_OPEN_MAX_CALLS,
        )

        # 运行时统计
        self._total_requests = 0
        self._success_requests = 0
        self._failed_requests = 0

        # 可取消的任务句柄（stop 时清理）
        self._background_tasks: List[asyncio.Task] = []

        # Message bus for event publishing (lazy-started)
        self._message_bus: Optional[MessageBus] = None
        self._message_bus_started = False
        self._message_bus_available = True

        log.info(
            f"Agent initializing | agent_name={self.agent_name} "
            f"agent_id={self.agent_id}"
        )

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def status(self) -> AgentStatus:
        """当前运行状态"""
        return self._status

    @status.setter
    def status(self, value: AgentStatus) -> None:
        old = self._status
        self._status = value
        if old != value:
            log.audit(
                f"Agent status changed | agent={self.agent_name} "
                f"agent_id={self.agent_id} old={old.value} new={value.value}"
            )

    @property
    def fuse_state(self) -> FuseState:
        """熔断器当前状态"""
        return self._fuse.state

    @property
    def is_fuse_open(self) -> bool:
        """熔断器是否处于打开状态"""
        return self._fuse.state == FuseState.OPEN

    # ------------------------------------------------------------------
    # 生命周期方法
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(self) -> None:
        """Agent 启动方法

        子类实现具体的启动逻辑（如订阅消息队列、启动 HTTP 服务等）。
        启动完成后应将状态置为 RUNNING 或 IDLE。
        """
        raise NotImplementedError

    async def handle_event(self, event: AgentEventModel) -> Dict[str, Any]:
        """统一事件/消息处理入口

        对外暴露的标准处理方法，内置以下通用逻辑：
        1. 状态检查（非 RUNNING/IDLE 状态拒绝处理）
        2. 熔断检查（熔断时直接返回降级响应）
        3. 异常捕获（统一包装为 AgentHandleFailedError）
        4. 日志埋点（audit 记录入参、出参、耗时、状态）
        5. 熔断计数更新（成功/失败）

        Args:
            event: AgentEventModel 标准事件模型

        Returns:
            处理结果字典，统一包含 success / code / message / data 字段
        """
        start_time = time.perf_counter()
        self._total_requests += 1

        # trace_id 透传
        if event.trace_id:
            TraceContext.set_trace_id(event.trace_id)

        log.audit(
            f"Agent handle_event start | agent={self.agent_name} "
            f"event_type={event.event_type.value} event_id={event.event_id}"
        )

        # 1) 状态检查
        if self._status not in (AgentStatus.RUNNING, AgentStatus.IDLE, AgentStatus.BUSY):
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            log.warning(
                f"Agent not ready | agent={self.agent_name} "
                f"status={self._status.value}"
            )
            return {
                "success": False,
                "code": "5001",
                "message": f"Agent 未就绪，当前状态: {self._status.value}",
                "data": None,
                "latency_ms": latency_ms,
            }

        # 2) 熔断检查
        fuse_check = self._check_fuse()
        if fuse_check:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            log.audit(
                f"Agent fuse triggered | agent={self.agent_name} "
                f"fuse_state={self._fuse.state.value}"
            )
            return {
                "success": False,
                "code": "2003",
                "message": f"熔断器已触发: {self._fuse.state.value}",
                "data": None,
                "latency_ms": latency_ms,
            }

        old_status = self._status
        self.status = AgentStatus.BUSY

        try:
            # 3) 执行具体业务逻辑
            result = await self._on_event(event)

            # 4) 记录成功
            self._on_success()
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            log.audit(
                f"Agent handle_event success | agent={self.agent_name} "
                f"event_type={event.event_type.value} latency_ms={latency_ms}"
            )

            # 统一包装响应
            if isinstance(result, dict) and "success" in result:
                response = result
            else:
                response = {
                    "success": True,
                    "code": "0000",
                    "message": "处理成功",
                    "data": result,
                }
            response["latency_ms"] = latency_ms
            return response

        except ProjectBaseException as exc:
            # 5) 项目标准异常 — 直接透传
            self._on_failure()
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            log.error(
                f"Agent handle_event business error | agent={self.agent_name} "
                f"error_code={exc.error_code.value} message={exc.message}"
            )
            return {
                "success": False,
                "code": exc.error_code.value,
                "message": exc.message,
                "data": exc.detail,
                "latency_ms": latency_ms,
            }

        except Exception as exc:
            # 6) 未知异常 — 包装为 AgentHandleFailedError，禁止裸抛
            self._on_failure()
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            tb = traceback.format_exc()
            log.error(
                f"Agent handle_event unexpected error | agent={self.agent_name} "
                f"exc={type(exc).__name__}: {exc}\n{tb}"
            )
            wrapped = AgentHandleFailedError(
                message=f"Agent 处理异常: {exc}",
                detail={"exception_type": type(exc).__name__, "traceback": tb},
            )
            return {
                "success": False,
                "code": wrapped.error_code.value,
                "message": wrapped.message,
                "data": wrapped.detail,
                "latency_ms": latency_ms,
            }

        finally:
            self.status = old_status

    @abstractmethod
    async def _on_event(self, event: AgentEventModel) -> Any:
        """具体的事件处理逻辑，由子类实现

        Args:
            event: 标准化事件模型

        Returns:
            任意业务结果，由 handle_event 统一包装为响应字典
        """
        raise NotImplementedError

    async def stop(self) -> None:
        """Agent 停止、资源释放方法

        取消所有后台任务，释放连接资源，将状态置为 STOPPED。
        子类可覆盖此方法以执行额外的清理逻辑，但必须调用 super().stop()。
        """
        log.audit(
            f"Agent stopping | agent={self.agent_name} "
            f"total={self._total_requests} success={self._success_requests} "
            f"failed={self._failed_requests}"
        )
        self.status = AgentStatus.STOPPING

        # 取消后台任务
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._background_tasks.clear()

        if self._message_bus_started and self._message_bus is not None:
            await self._message_bus.stop()
            self._message_bus_started = False
        self.status = AgentStatus.STOPPED

        log.info(f"Agent stopped | agent={self.agent_name} agent_id={self.agent_id}")

    # ------------------------------------------------------------------
    # 熔断器内部逻辑
    # ------------------------------------------------------------------

    def _check_fuse(self) -> bool:
        """检查熔断器状态，返回 True 表示请求应被拦截"""
        result = self._fuse.should_reject()
        if self._fuse.state == FuseState.HALF_OPEN and not result:
            log.warning(f"Agent fuse half-open | agent={self.agent_name}")
        return result

    def _on_success(self) -> None:
        """请求成功后的熔断器状态更新"""
        self._success_requests += 1
        old_state = self._fuse.state
        self._fuse.on_success()
        if old_state == FuseState.HALF_OPEN:
            log.info(f"Agent fuse closed (recovered) | agent={self.agent_name}")
        elif old_state == FuseState.CLOSED and self._fuse._failure_count == 0:
            log.debug(f"Agent fuse failure count reset | agent={self.agent_name}")

    def _on_failure(self) -> None:
        """请求失败后的熔断器状态更新"""
        self._failed_requests += 1
        old_state = self._fuse.state
        self._fuse.on_failure()
        if old_state == FuseState.HALF_OPEN:
            log.error(
                f"Agent fuse re-opened | agent={self.agent_name} "
                f"failure_count={self._fuse._failure_count}"
            )
        elif old_state == FuseState.CLOSED and self._fuse.state == FuseState.OPEN:
            log.error(
                f"Agent fuse opened | agent={self.agent_name} "
                f"threshold={self.FUSE_FAILURE_THRESHOLD} "
                f"failure_count={self._fuse._failure_count}"
            )

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def add_background_task(self, task: asyncio.Task) -> None:
        """注册后台任务，stop() 时自动取消

        自动添加异常回调：后台任务抛未捕获异常时记录日志并触发熔断计数，
        禁止异常向上抛到事件循环导致 Agent 进程崩溃。
        """
        task.add_done_callback(self._on_background_task_done)
        self._background_tasks.append(task)

    async def publish(
        self,
        event_type: AgentEventTypeEnum,
        payload: Dict[str, Any],
        target_agent: Optional[str] = None,
        priority: int = 1,
    ) -> None:
        """Publish an Agent event to the message bus."""
        if not self._message_bus_available:
            return

        try:
            if self._message_bus is None:
                self._message_bus = MessageBusFactory.create()

            if not self._message_bus_started:
                await self._message_bus.start()
                self._message_bus_started = True

            event = AgentEventModel(
                event_id=uuid.uuid4().hex,
                event_type=event_type,
                source_agent=self.agent_name,
                target_agent=target_agent,
                payload=payload,
                priority=priority,
            )
            await self._message_bus.send_message(redis_settings.stream_topic, event)
            log.debug(
                f"Event published | agent={self.agent_name} "
                f"event_type={event_type.value}"
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._message_bus_available = False
            log.error(
                f"Message bus publish failed | agent={self.agent_name} "
                f"event_type={event_type.value} exc={type(exc).__name__}: {exc}"
            )
            raise

    def _on_background_task_done(self, task: asyncio.Task) -> None:
        """后台任务完成回调：捕获并记录异常"""
        if not task.cancelled() and (exc := task.exception()):
            self._failed_requests += 1
            log.error(
                f"Background task failed | agent={self.agent_name} "
                f"exc={type(exc).__name__}: {exc}"
            )

    def get_stats(self) -> Dict[str, Any]:
        """获取 Agent 运行时统计信息"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self._status.value,
            "fuse_state": self._fuse.state.value,
            "fuse_failure_count": self._fuse._failure_count,
            "total_requests": self._total_requests,
            "success_requests": self._success_requests,
            "failed_requests": self._failed_requests,
        }

    def _health_check(self) -> Dict[str, Any]:
        """健康检查（可覆盖）

        默认检查项：Agent 状态、熔断器状态、后台任务存活状态。
        子类覆盖时应先调用 super()._health_check() 再扩展自定义检查项。

        Returns:
            healthy: 全部检查项通过时为 True，任意一项异常则为 False
        """
        # 1. Agent 状态正常
        status_ok = self._status in (
            AgentStatus.RUNNING,
            AgentStatus.IDLE,
            AgentStatus.BUSY,
        )
        # 2. 熔断器未处于 OPEN 状态
        fuse_ok = self._fuse.state != FuseState.OPEN
        # 3. 后台任务无未捕获异常（已崩溃的任务）
        tasks_ok = all(
            not t.done()
            or (t.done() and t.exception() is None and not t.cancelled())
            for t in self._background_tasks
        )

        healthy = status_ok and fuse_ok and tasks_ok
        return {
            "healthy": healthy,
            "status": self._status.value,
            "fuse_state": self._fuse.state.value,
            "status_ok": status_ok,
            "fuse_ok": fuse_ok,
            "tasks_ok": tasks_ok,
            "background_tasks_count": len(self._background_tasks),
        }


__all__ = [
    "AgentStatus",
    "FuseState",
    "AgentRegistry",
    "BaseAgent",
]
