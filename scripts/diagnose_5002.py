"""诊断 5002 路由处理失败错误。"""
import asyncio
import json
import sys
import traceback

async def main():
    # 1. 测试 JWT 解析
    from src.agents.router_agent.auth import parse_jwt_user
    jwt = '{"user_id":"dev_user","role_type":"enterprise_admin","exp":9999999999}'
    try:
        user = parse_jwt_user(f"Bearer {jwt}")
        print(f"[OK] JWT parsed: user_id={user.user_id} role={user.user_role}")
    except Exception as e:
        print(f"[FAIL] JWT parse: {e}")
        traceback.print_exc()
        return

    # 2. 测试会话创建
    from src.agents.router_agent.context_manager import context_manager_singleton as cm
    session = await cm.create_session(session_id="TEST001", user_id="dev_user")
    print(f"[OK] Session created: {session.session_id}")

    # 3. 测试 upsert_user_message
    from src.core.schemas import UserRoleEnum
    session_state = await cm.upsert_user_message(
        session_id="TEST001",
        user_id="dev_user",
        user_role=UserRoleEnum.ENTERPRISE_ADMIN,
        user_message="今天店里有多少违规抓拍",
    )
    print(f"[OK] upsert_user_message: chat_history_size={len(session_state.chat_history)}")

    # 4. 测试路由
    from src.agents.router_agent.router_service import RouterService
    rs = RouterService.get_instance()
    try:
        route_result = await rs.route(
            message="今天店里有多少违规抓拍",
            user_role=UserRoleEnum.ENTERPRISE_ADMIN,
            chat_history=[msg.model_dump(mode="json") for msg in session_state.chat_history],
        )
        print(f"[OK] Route: intent={route_result.intent_type.value} target={route_result.target_agent} confidence={route_result.intent_confidence}")
    except Exception as e:
        print(f"[FAIL] Router.route(): {e}")
        traceback.print_exc()
        return

    # 5. 测试 ChatMessageResponse 构造
    from src.core.schemas import ChatMessageResponse, ConfirmationModel, ActionTypeEnum, beijing_now, generate_id
    from src.core.logger import TraceContext
    trace_id = TraceContext.get_trace_id()
    response_type = "answer"
    answer_payload = "收到，我正在帮你查询对应数据。"

    try:
        response = ChatMessageResponse(
            code="0000",
            message="ok",
            success=True,
            trace_id=trace_id,
            response_time=beijing_now(),
            data={"request_id": None, "user_id": "dev_user"},
            session_id="TEST001",
            response_type=response_type,
            answer_payload=answer_payload,
            structured_summary={
                "session_history_size": len(session_state.chat_history),
                "intent_type": route_result.intent_type.value,
                "intent_confidence": route_result.intent_confidence,
                "target_agent": route_result.target_agent,
                "target_tool": route_result.target_tool,
                "tool_args": route_result.tool_args,
                "slots": route_result.slots,
                "dispatch_status": "planned",
            },
            guidance_type="none",
            suggested_actions=[],
            pending_confirmation=None,
        )
        print(f"[OK] ChatMessageResponse constructed: type={response.response_type}")
    except Exception as e:
        print(f"[FAIL] ChatMessageResponse construction: {e}")
        traceback.print_exc()
        return

    # 6. 测试 model_dump
    try:
        dumped = response.model_dump(mode="json")
        print(f"[OK] model_dump: keys={list(dumped.keys())}")
        print(f"     response_type={dumped.get('response_type')} code={dumped.get('code')}")
    except Exception as e:
        print(f"[FAIL] model_dump: {e}")
        traceback.print_exc()
        return

    print("\n=== ALL CHECKS PASSED ===")

if __name__ == "__main__":
    asyncio.run(main())
