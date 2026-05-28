"""
大模型客户端模块 (llm_client.py)

提供异步 LLM 调用客户端、指数退避重试工具、以及审计装饰器。
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from src.core.schemas import beijing_now
from openai import (
    AsyncOpenAI,
    APIError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
)

from src.core.config import llm_settings, LLMSettings
from src.core.circuit_breaker import ProviderFuseManager
from src.core.exceptions import LLMCallFailedError, LLMFuseTriggeredError, LLMResponseInvalidError
from src.core.logger import log

T = TypeVar("T")


async def with_retry(
    func: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retryable_exceptions: Tuple[type, ...] = (
        APIError,
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
    ),
) -> T:
    """异步重试装饰器，指数退避

    Args:
        func: 无参数异步函数，封装要重试的操作
        max_retries: 最大重试次数（不含首次尝试）
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
        retryable_exceptions: 触发重试的异常类型元组
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except retryable_exceptions as e:
            last_exception = e
            if attempt >= max_retries:
                break
            delay = min(base_delay * (2 ** attempt), max_delay)
            await asyncio.sleep(delay)
    raise last_exception


def audit_llm_call(event_type: str):
    """LLM/VLM 调用审计装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            trace_id = kwargs.get("trace_id")
            if trace_id is None and len(args) >= 2:
                trace_id = args[1]
            trace_id = trace_id or ""

            start_time = beijing_now()
            try:
                result = await func(self, *args, **kwargs)
                latency_ms = int((beijing_now() - start_time).total_seconds() * 1000)

                output_data = {}
                if hasattr(result, "model_dump"):
                    output_data = result.model_dump()
                elif isinstance(result, str):
                    output_data = {"content": result}
                else:
                    output_data = {"result": str(result)}

                log.audit(
                    f"{event_type} completed",
                    trace_id=trace_id,
                    success=True,
                    latency_ms=latency_ms,
                    input_data={k: v for k, v in kwargs.items() if k != "self"},
                    output_data=output_data,
                )
                return result
            except Exception as e:
                latency_ms = int((beijing_now() - start_time).total_seconds() * 1000)
                log.audit(
                    f"{event_type} failed",
                    trace_id=trace_id,
                    success=False,
                    latency_ms=latency_ms,
                    error_code=getattr(getattr(e, "error_code", None), "value", "2001"),
                    error_message=str(e),
                )
                raise
        return wrapper
    return decorator


class AsyncLLMClient:
    """异步大模型调用客户端

    集成熔断器、指数退避重试、审计日志，支持上下文管理器用法。
    """

    def __init__(self, settings: Optional[LLMSettings] = None):
        self._settings = settings or llm_settings
        self._fuse_manager = ProviderFuseManager()
        self._openai = AsyncOpenAI(
            api_key=self._settings.llm_api_key,
            base_url=self._settings.llm_base_url,
            timeout=self._settings.llm_timeout,
            max_retries=0,
        )

    @audit_llm_call("llm_call")
    async def chat(
        self,
        messages,
        trace_id,
        provider_id="default",
        temperature=0.7,
        max_tokens=None,
        return_response_object=False,
        **extra_params
    ):
        """发起对话请求

        Args:
            messages: 消息列表
            trace_id: 链路追踪 ID
            provider_id: 模型提供者标识
            temperature: 采样温度
            max_tokens: 最大生成 token 数
            **extra_params: 额外参数

        Returns:
            模型生成的文本内容

        Raises:
            LLMFuseTriggeredError: 熔断器开启时直接拒绝
            LLMResponseInvalidError: 响应格式异常
            LLMCallFailedError: 调用最终失败
        """
        # 1. 熔断检查
        fuse = self._fuse_manager.get_fuse(provider_id, prefix="llm", failure_threshold=3)
        if fuse.should_reject():
            raise LLMFuseTriggeredError(f"LLM provider '{provider_id}' fuse is OPEN")

        # 2. 构建请求
        async def _call():
            response = await self._openai.chat.completions.create(
                model=self._settings.llm_model_name or provider_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
            )
            if not response.choices:
                raise LLMResponseInvalidError("Empty choices in LLM response")
            if return_response_object:
                return response

            content = response.choices[0].message.content
            if content is None:
                raise LLMResponseInvalidError("Null content in LLM response")
            return content

        # 3. 带重试调用
        try:
            result = await with_retry(
                _call,
                max_retries=self._settings.llm_max_retries or 3,
                retryable_exceptions=(APIError, RateLimitError, APITimeoutError, APIConnectionError),
            )
            fuse.on_success()
            return result
        except LLMFuseTriggeredError:
            raise
        except LLMResponseInvalidError:
            fuse.on_failure()
            raise
        except Exception as e:
            fuse.on_failure()
            raise LLMCallFailedError(f"LLM call failed after retries: {e}") from e

    async def close(self) -> None:
        """关闭客户端连接"""
        await self._openai.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


__all__ = ["with_retry", "audit_llm_call", "AsyncLLMClient"]
