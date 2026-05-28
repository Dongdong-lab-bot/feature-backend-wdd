"""
统一通信抽象层 (message_bus.py)

提供与底层 MQ 实现解耦的标准消息收发接口。
当前基于 Redis Streams 实现，预留切换 Kafka / RabbitMQ 的扩展空间。

设计原则：
- 业务层只依赖 MessageBus 抽象，不依赖具体实现
- 通过 MessageBusFactory 创建实例，切换 MQ 只需改配置
- 消费者组模式支持负载均衡与 at-least-once 投递
"""

from __future__ import annotations

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from pydantic import BaseModel

from src.core.logger import log
from src.core.config import redis_settings


# ---------------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------------

class MessageBus(ABC):
    """消息总线抽象基类

    所有底层 MQ 实现必须继承此类，提供统一的发送/订阅接口。
    """

    @abstractmethod
    async def start(self) -> None:
        """启动消息总线（建立连接、初始化资源）"""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """停止消息总线（释放连接、清理资源）"""
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, topic: str, data: BaseModel) -> str:
        """发送消息到指定 topic

        Args:
            topic: 消息主题 / Stream 名称
            data: Pydantic 模型实例，自动序列化为 JSON

        Returns:
            消息唯一标识（如 Redis Stream Entry ID）
        """
        raise NotImplementedError

    @abstractmethod
    async def subscribe_topic(
        self,
        topic: str,
        callback: Callable[[Dict[str, Any]], Union[Any, Awaitable[Any]]],
        group: Optional[str] = None,
        consumer: Optional[str] = None,
    ) -> None:
        """订阅指定 topic 的消息

        Args:
            topic: 消息主题 / Stream 名称
            callback: 消息处理回调，接收反序列化后的字典；
                      同步/异步函数均可；返回 True 或成功执行后自动 ACK
            group: 消费者组名称，为空则不使用消费者组（独立消费）
            consumer: 消费者名称，group 非空时必填
        """
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe_topic(self, topic: str) -> None:
        """取消订阅指定 topic"""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Redis Streams 实现
# ---------------------------------------------------------------------------

class RedisMessageBus(MessageBus):
    """基于 Redis Streams 的消息总线实现

    特性：
    - 支持独立消费者（xread）与消费者组（xreadgroup）两种模式
    - 自动 ACK：回调成功执行后自动确认；失败不确认，消息留在 PEL 中重投
    - 字段自动序列化/反序列化（JSON）
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: Optional[int] = None,
    ):
        self._host = host or redis_settings.redis_host
        self._port = port or redis_settings.redis_port
        self._password = password or redis_settings.redis_password
        self._db = db if db is not None else redis_settings.redis_db

        self._client: Optional[Any] = None
        self._subscribers: Dict[str, asyncio.Task] = {}
        self._running = False

    async def start(self) -> None:
        """建立 Redis 异步连接"""
        import redis.asyncio as aioredis

        self._client = aioredis.Redis(
            host=self._host,
            port=self._port,
            password=self._password,
            db=self._db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        await self._client.ping()
        self._running = True
        log.info(
            f"RedisMessageBus started | {self._host}:{self._port} db={self._db}"
        )

    async def stop(self) -> None:
        """取消所有订阅任务并关闭连接"""
        self._running = False

        for topic, task in list(self._subscribers.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            log.debug(f"Consume task cancelled | topic={topic}")

        self._subscribers.clear()

        if self._client:
            await self._client.close()
            self._client = None

        log.info("RedisMessageBus stopped")

    async def send_message(self, topic: str, data: BaseModel) -> str:
        """发送消息到 Redis Stream

        序列化策略：
        1. BaseModel → dict（Pydantic model_dump）
        2. dict 中所有非字符串值 → JSON 字符串
        3. 写入 Redis Stream
        """
        if not self._client:
            raise RuntimeError("MessageBus not started. Call start() first.")

        # 序列化为字典
        payload = data.model_dump(mode="json")

        # Redis Stream 字段值必须是字符串
        fields: Dict[str, str] = {}
        for key, value in payload.items():
            if isinstance(value, str):
                fields[key] = value
            else:
                fields[key] = json.dumps(value, ensure_ascii=False)

        msg_id = await self._client.xadd(topic, fields)  # type: ignore[union-attr]
        log.debug(f"Message sent | topic={topic} msg_id={msg_id}")
        return str(msg_id)

    async def subscribe_topic(
        self,
        topic: str,
        callback: Callable[[Dict[str, Any]], Union[Any, Awaitable[Any]]],
        group: Optional[str] = None,
        consumer: Optional[str] = None,
    ) -> None:
        """订阅 Redis Stream

        消费者组模式（推荐）：
        - 自动创建消费者组（若不存在）
        - 使用 xreadgroup 读取，支持负载均衡与故障转移
        - 回调成功后自动 xack

        独立消费者模式：
        - 使用 xread 读取，不保证只消费一次
        - 适用于广播、测试等场景
        """
        if not self._client:
            raise RuntimeError("MessageBus not started. Call start() first.")

        if topic in self._subscribers:
            log.warning(f"Already subscribed | topic={topic}")
            return

        # 消费者组模式下自动创建组
        if group:
            try:
                await self._client.xgroup_create(  # type: ignore[union-attr]
                    topic, group, id="0", mkstream=True
                )
                log.info(f"Consumer group created | topic={topic} group={group}")
            except Exception as exc:
                import redis.exceptions

                if isinstance(exc, redis.exceptions.ResponseError):
                    if exc.args and "BUSYGROUP" in str(exc.args[0]):
                        log.debug(
                            f"Consumer group already exists | topic={topic} group={group}"
                        )
                    else:
                        log.error(
                            f"Create consumer group failed | topic={topic} "
                            f"group={group} exc={exc}"
                        )
                        raise
                else:
                    log.error(
                        f"Create consumer group failed | topic={topic} "
                        f"group={group} exc={exc}"
                    )
                    raise

        # 启动后台消费任务
        task = asyncio.create_task(
            self._consume_loop(topic, callback, group, consumer),
            name=f"consumer-{topic}-{consumer or 'solo'}",
        )
        self._subscribers[topic] = task
        log.info(
            f"Subscribed | topic={topic} group={group} consumer={consumer}"
        )

    async def unsubscribe_topic(self, topic: str) -> None:
        """取消订阅并终止对应后台任务"""
        task = self._subscribers.pop(topic, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            log.info(f"Unsubscribed | topic={topic}")

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _consume_loop(
        self,
        topic: str,
        callback: Callable[[Dict[str, Any]], Union[Any, Awaitable[Any]]],
        group: Optional[str],
        consumer: Optional[str],
    ) -> None:
        """后台消费循环"""
        # 消费者组模式用 ">"（只读新消息），独立模式用 "$"（从最新开始）
        stream_id = ">" if group else "$"

        while self._running:
            try:
                if group and consumer:
                    messages = await self._client.xreadgroup(  # type: ignore[union-attr]
                        groupname=group,
                        consumername=consumer,
                        streams={topic: stream_id},
                        count=1,
                        block=1000,
                    )
                else:
                    messages = await self._client.xread(  # type: ignore[union-attr]
                        streams={topic: stream_id},
                        count=1,
                        block=1000,
                    )

                if not messages:
                    continue

                for _stream_name, msgs in messages:
                    for msg_id, fields in msgs:
                        await self._process_message(
                            topic, msg_id, fields, callback, group
                        )

            except asyncio.CancelledError:
                log.debug(f"Consume loop cancelled | topic={topic}")
                break
            except Exception as exc:
                log.error(f"Consume loop error | topic={topic} exc={exc}")
                await asyncio.sleep(1)

    async def _process_message(
        self,
        topic: str,
        msg_id: str,
        fields: Dict[str, str],
        callback: Callable[[Dict[str, Any]], Union[Any, Awaitable[Any]]],
        group: Optional[str],
    ) -> None:
        """处理单条消息：反序列化 → 回调 → ACK"""
        # 反序列化
        data: Dict[str, Any] = {"__msg_id": msg_id, "__topic": topic}
        for key, value in fields.items():
            if key.startswith("__"):
                continue
            try:
                data[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                data[key] = value

        try:
            # 执行回调（支持同步/异步）
            import inspect

            if inspect.iscoroutinefunction(callback):
                result = await callback(data)
            else:
                result = await asyncio.to_thread(callback, data)

            # 消费者组模式下自动 ACK
            if group:
                await self._client.xack(topic, group, msg_id)  # type: ignore[union-attr]
                log.debug(f"Message acked | topic={topic} msg_id={msg_id}")

        except Exception as exc:
            log.error(
                f"Message processing failed | topic={topic} msg_id={msg_id} "
                f"exc={type(exc).__name__}: {exc}"
            )
            # 不 ACK，消息留在 PEL 中等待重投


# ---------------------------------------------------------------------------
# 工厂
# ---------------------------------------------------------------------------

class MessageBusFactory:
    """消息总线工厂

    通过配置创建对应的消息总线实例，业务层无需关心底层实现。
    """

    _registry: Dict[str, type] = {
        "redis": RedisMessageBus,
    }

    @classmethod
    def register(cls, name: str, impl: type) -> None:
        """注册新的消息总线实现（扩展点）"""
        cls._registry[name] = impl
        log.info(f"MessageBus implementation registered: {name}")

    @classmethod
    def create(cls, bus_type: str = "redis", **kwargs: Any) -> MessageBus:
        """创建消息总线实例

        Args:
            bus_type: 总线类型，当前支持 "redis"
            **kwargs: 传递给具体实现的构造参数

        Returns:
            MessageBus 实例
        """
        impl = cls._registry.get(bus_type)
        if not impl:
            raise ValueError(
                f"Unknown message bus type: {bus_type}. "
                f"Available: {list(cls._registry.keys())}"
            )
        return impl(**kwargs)

    @classmethod
    def available_types(cls) -> list:
        """获取所有已注册的消息总线类型"""
        return list(cls._registry.keys())


__all__ = [
    "MessageBus",
    "RedisMessageBus",
    "MessageBusFactory",
]
