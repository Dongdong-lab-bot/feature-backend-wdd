"""验证 DeepSeek API 连通性。"""
import asyncio
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，确保能 import src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.llm_client import AsyncLLMClient

async def main():
    print("正在连接 DeepSeek V4 ...")
    c = AsyncLLMClient()
    r = await c.chat(
        [{"role": "user", "content": "一句话介绍食品安全管理"}],
        trace_id="verify_deepseek",
    )
    print(f"✅ DeepSeek V4 连接成功")
    print(f"   回复: {r[:100]}...")
    await c.close()

if __name__ == "__main__":
    asyncio.run(main())
