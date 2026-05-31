## 现有 AI 接口情况

__已经有的：__

- `.env` 里已经配置了 DeepSeek API Key（`sk-941ecb651a714579992a8b47f3d6f042`）
- `src/core/llm_client.py` — 完整的异步 LLM 客户端，支持重试、熔断、审计日志
- `src/core/config.py` — 配置管理，从 `.env` 读取 LLM 配置
- 模型用的是 `deepseek-reasoner`（DeepSeek 推理模型）
