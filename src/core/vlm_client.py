"""全局异步视觉大模型客户端"""

from typing import Any, Optional

from openai import (
    AsyncOpenAI,
    APIError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
)

from src.core.config import llm_settings, LLMSettings
from src.core.circuit_breaker import ProviderFuseManager
from src.core.exceptions import LLMCallFailedError, LLMFuseTriggeredError, LLMResponseInvalidError
from src.core.llm_client import with_retry, audit_llm_call


class AsyncVLMClient:
    """全局异步视觉大模型客户端

    与 AsyncLLMClient 共享配置，但熔断器、审计、接口完全隔离。
    """

    def __init__(self, settings: Optional[LLMSettings] = None):
        self._settings = settings or llm_settings
        # VLM 使用独立的熔断器管理器（prefix="vlm" 确保与 LLM 隔离）
        self._fuse_manager = ProviderFuseManager()
        self._openai = AsyncOpenAI(
            api_key=self._settings.llm_api_key,
            base_url=self._settings.llm_base_url,
            timeout=self._settings.llm_timeout,
            max_retries=0,
        )

    @audit_llm_call("vlm_verify")
    async def verify_image(
        self,
        image_url: str,
        prompt: str,
        trace_id: str,
        provider_id: str = "default",
        temperature: float = 0.3,
        max_tokens: Optional[int] = 512,
        **extra_params: Any,
    ) -> str:
        """发送图片到 VLM 进行分析

        Args:
            image_url: 图片 URL（支持 http/https/base64）
            prompt: 分析指令
            trace_id: 全链路追踪 ID
            provider_id: 提供商标识
            temperature: 采样温度（VLM 通常更低，减少幻觉）
            max_tokens: 最大生成 token 数

        Returns:
            模型分析结果文本
        """
        fuse = self._fuse_manager.get_fuse(provider_id, prefix="vlm", failure_threshold=3)

        if fuse.should_reject():
            raise LLMFuseTriggeredError(f"VLM provider '{provider_id}' fuse is OPEN")

        # 构建 OpenAI 兼容的多模态消息
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        async def _call():
            response = await self._openai.chat.completions.create(
                model=self._settings.llm_model_name or provider_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
            )
            if not response.choices:
                raise LLMResponseInvalidError("Empty choices in VLM response")
            content = response.choices[0].message.content
            if content is None:
                raise LLMResponseInvalidError("Null content in VLM response")
            return content

        try:
            result = await with_retry(
                _call,
                max_retries=self._settings.llm_max_retries or 3,
                retryable_exceptions=(
                    APIError,
                    RateLimitError,
                    APITimeoutError,
                    APIConnectionError,
                ),
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
            raise LLMCallFailedError(f"VLM call failed after retries: {e}") from e

    async def close(self) -> None:
        await self._openai.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


__all__ = ["AsyncVLMClient"]
