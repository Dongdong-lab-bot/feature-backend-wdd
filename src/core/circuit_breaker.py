"""
Circuit Breaker 独立组件 (circuit_breaker.py)

将熔断器状态机提取为可复用组件，供 BaseAgent、LLMClient、VLMClient 等使用。

状态机：
    CLOSED(正常) → OPEN(熔断) → HALF_OPEN(试探) → CLOSED(恢复)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from src.core.logger import log


class FuseState(str, Enum):
    """熔断器状态枚举

    CLOSED    — 正常状态，请求正常通过
    OPEN      — 熔断状态，请求直接失败/降级
    HALF_OPEN — 半开状态，允许少量请求试探恢复
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """熔断器

    独立的状态机组件，按 name 区分实例，支持自定义阈值参数。
    """

    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3

    # 内部状态（field 声明避免 dataclass 将其视为构造参数）
    _state: FuseState = field(init=False, default=FuseState.CLOSED)
    _failure_count: int = field(init=False, default=0)
    _last_failure_time: Optional[float] = field(init=False, default=None)
    _half_open_calls: int = field(init=False, default=0)
    _lock: threading.Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()

    def should_reject(self) -> bool:
        """检查当前请求是否应被拒绝

        Returns:
            True  表示请求应被拦截（OPEN 且未超时，或 HALF_OPEN 试探已满）
            False 表示请求可以通过
        """
        with self._lock:
            now = time.monotonic()

            if self._state == FuseState.CLOSED:
                return False

            if self._state == FuseState.OPEN:
                if (
                    self._last_failure_time is not None
                    and (now - self._last_failure_time) >= self.recovery_timeout
                ):
                    self._state = FuseState.HALF_OPEN
                    self._half_open_calls = 0
                    log.warning(f"Fuse half-open | name={self.name}")
                    return False
                return True

            if self._state == FuseState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    return True
                self._half_open_calls += 1
                return False

            return False

    def on_success(self) -> None:
        """请求成功后的状态更新"""
        with self._lock:
            if self._state == FuseState.HALF_OPEN:
                self._state = FuseState.CLOSED
                self._failure_count = 0
                self._half_open_calls = 0
                log.info(f"Fuse closed (recovered) | name={self.name}")
            elif self._state == FuseState.CLOSED:
                if self._failure_count > 0:
                    self._failure_count = 0
                    log.debug(f"Fuse failure count reset | name={self.name}")

    def on_failure(self) -> None:
        """请求失败后的状态更新"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == FuseState.HALF_OPEN:
                self._state = FuseState.OPEN
                self._half_open_calls = 0
                log.error(
                    f"Fuse re-opened | name={self.name} "
                    f"failure_count={self._failure_count}"
                )
            elif (
                self._state == FuseState.CLOSED
                and self._failure_count >= self.failure_threshold
            ):
                self._state = FuseState.OPEN
                log.error(
                    f"Fuse opened | name={self.name} "
                    f"threshold={self.failure_threshold} "
                    f"failure_count={self._failure_count}"
                )

    @property
    def state(self) -> FuseState:
        """熔断器当前状态"""
        return self._state

    @property
    def failure_count(self) -> int:
        """当前连续失败次数"""
        return self._failure_count

    @property
    def last_failure_time(self) -> Optional[float]:
        """最后一次失败的时间戳（monotonic）"""
        return self._last_failure_time

    @property
    def half_open_calls(self) -> int:
        """半开状态下已发出的试探请求数"""
        return self._half_open_calls


class ProviderFuseManager:
    """按 provider_id 管理熔断器实例

    为每个 provider_id 维护独立的 CircuitBreaker，支持按 prefix 隔离命名空间。
    """

    def __init__(self) -> None:
        self._fuses: Dict[str, CircuitBreaker] = {}

    def get_fuse(
        self,
        provider_id: str,
        prefix: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ) -> CircuitBreaker:
        """获取或创建指定 provider 的熔断器

        Args:
            provider_id: 提供者唯一标识
            prefix: 命名空间前缀，用于隔离不同场景下的熔断器
            failure_threshold: 熔断触发阈值
            recovery_timeout: 熔断恢复超时（秒）
            half_open_max_calls: 半开状态最大试探次数

        Returns:
            该 provider 对应的 CircuitBreaker 实例（复用已有或新建）
        """
        key = f"{prefix}:{provider_id}"
        if key not in self._fuses:
            self._fuses[key] = CircuitBreaker(
                name=key,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                half_open_max_calls=half_open_max_calls,
            )
        return self._fuses[key]

    def clear(self) -> None:
        """清空所有熔断器（仅测试使用）"""
        self._fuses.clear()

    def list_fuses(self) -> Dict[str, CircuitBreaker]:
        """获取所有已创建的熔断器副本"""
        return self._fuses.copy()


__all__ = ["FuseState", "CircuitBreaker", "ProviderFuseManager"]
