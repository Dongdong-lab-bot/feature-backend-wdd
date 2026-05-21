"""直接模拟 API 调用链，定位 5002 真正错误。"""
import asyncio
import json
import os
import sys
import traceback

# 设置 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.chat_router import handle_chat_router, ChatRouterPayload
from src.api.routes.chat import _build_chat_response_from_router_result
from src.core.logger import TraceContext

async def main():
    # 设置 trace_id
    TraceContext.set_trace_id("a" * 32)

    # Step 1: 构造 payload（模拟 API 传入参数）
    jwt = '{"user_id":"dev_user","role_type":"enterprise_admin","exp":9999999999}'
    payload = ChatRouterPayload(
        session_id="T1",
        message="今天店里有多少违规抓拍",
        authorization=f"Bearer {jwt}",
    )
    print(f"[OK] Payload created: session_id={payload.session_id}")

    # Step 2: 调用 handle_chat_router
    try:
        result = await handle_chat_router(payload)
        print(f"[OK] handle_chat_router returned: type={type(result).__name__}")
        print(f"     keys={list(result.keys())}")
        print(f"     code={result.get('code')} response_type={result.get('response_type')}")
        print(f"     trace_id={result.get('trace_id')}")
        print(f"     session_id={result.get('session_id')}")
    except Exception as e:
        print(f"[FAIL] handle_chat_router raised: {e}")
        traceback.print_exc()
        return

    # Step 3: 验证是否能通过 _build_chat_response_from_router_result
    try:
        response = _build_chat_response_from_router_result(
            result=result,
            session_id="T1",
            user_id="dev_user",
        )
        print(f"[OK] response built: type={response.response_type} code={response.code} success={response.success}")
    except Exception as e:
        print(f"[FAIL] _build_chat_response_from_router_result failed: {e}")
        traceback.print_exc()
        # 打印详细字段
        print(f"Result keys: {list(result.keys())}")
        print(f"Result: {json.dumps(result, ensure_ascii=False, default=str)[:500]}")
        return

    # Step 4: 验证 model_dump 是否能序列化
    try:
        dumped = response.model_dump(mode="json")
        print(f"[OK] model_dump: {list(dumped.keys())}")
    except Exception as e:
        print(f"[FAIL] model_dump: {e}")
        traceback.print_exc()
        return

    # Step 5: 验证 Pydantic JSON 序列化（FastAPI 内部使用的）
    try:
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        print(f"[OK] model_dump_json: {list(parsed.keys())}")
        print(f"     code={parsed.get('code')} response_type={parsed.get('response_type')} session_id={parsed.get('session_id')}")
    except Exception as e:
        print(f"[FAIL] model_dump_json: {e}")
        traceback.print_exc()
        return

    print("\n=== ALL PASSED ===")

if __name__ == "__main__":
    asyncio.run(main())
