"""DataAgent main implementation with scene-dispatch architecture."""

from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ErrorCodeEnum, ProjectBaseException
from src.core.sql_validator import SQLGuard, SQLGuardConfig

from .audit import audit_log
from .models import HandlerContext
from .response import standard_response
from .scene_handlers import SCENE_HANDLER_REGISTRY
from .sql_validator.adapter import wrap_security_check


class DataAgent(BaseAgent):
    """DataAgent implementation based on BaseAgent contract."""

    _ALLOWED_ROLES = {"guest", "store_manager", "supervisor", "admin"}

    def __init__(self, agent_id: str = "data_agent_01"):
        super().__init__(agent_id=agent_id, agent_name="data_agent")
        self._sql_guard = SQLGuard(
            config=SQLGuardConfig(
                custom_validators=[wrap_security_check],
                # 性能规则交给我们自己的 _performance_check() 处理
                # （SQLGuard 默认 require_limit_on_tables={"*"} 会拦截无 LIMIT 的 SQL，
                #  但我们是自动补 LIMIT 而非拦截，所以关掉 SQLGuard 的性能规则）
                require_where_on_tables=set(),
                require_limit_on_tables=set(),
            )
        )

    async def run(self) -> None:
        """BaseAgent explicit lifecycle start."""
        pass

    async def _on_event(self, event: Any) -> Any:
        """Handle incoming event payload directly via food safety flow."""
        payload = event.payload if hasattr(event, "payload") else dict(event)
        return await self.query_food_safety_data(
            user_query=str(payload.get("user_query", "")),
            scene=str(payload.get("scene", "alarm_query")),
            context=payload.get("context"),
        )

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent compatibility entry."""
        return await self.query_food_safety_data(
            user_query=str(payload.get("user_query", "")),
            scene=str(payload.get("scene", "alarm_query")),
            context=payload.get("context"),
        )

    async def query_food_safety_data(
        self,
        user_query: str,
        scene: str = "alarm_query",
        context: HandlerContext | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Unified async entry for multi-scene food safety data query."""
        normalized_scene = (scene or "").strip().lower()
        if not normalized_scene:
            return standard_response(
                error_code=ErrorCodeEnum.PARAM_ERROR,
                data="",
                message="scene 不能为空",
            )

        if context is None:
            context = {
                "trace_id": uuid4().hex,
                "user_role": "guest",
                "store_ids": [],
                "chat_history": [],
            }

        try:
            ctx = context if isinstance(context, HandlerContext) else HandlerContext(**context)
        except ValidationError as exc:
            return standard_response(
                error_code=ErrorCodeEnum.PARAM_ERROR,
                data="",
                message="context 参数不合法",
                trace_id=context.get("trace_id", "") if isinstance(context, dict) else "",
                detail={"error": str(exc)},
            )

        if not user_query.strip():
            return standard_response(
                error_code=ErrorCodeEnum.PARAM_ERROR,
                data="",
                message="user_query 不能为空",
                trace_id=ctx.trace_id,
            )

        if ctx.user_role not in self._ALLOWED_ROLES:
            return standard_response(
                error_code=ErrorCodeEnum.PERMISSION_DENIED,
                data="",
                message="用户角色无权限调用该Tool",
                trace_id=ctx.trace_id,
                detail={"user_role": ctx.user_role},
            )

        handler_cls = SCENE_HANDLER_REGISTRY.get(normalized_scene)
        if handler_cls is None:
            return standard_response(
                error_code=ErrorCodeEnum.PARAM_ERROR,
                data="",
                message=f"未支持的场景: {normalized_scene}",
                trace_id=ctx.trace_id,
            )

        handler = handler_cls(publisher=self.publish, sql_guard=self._sql_guard)
        try:
            audit_log(
                operator="data_agent",
                action="scene_route",
                input_data=normalized_scene,
                output_data="matched",
                success=True,
                trace_id=ctx.trace_id,
            )
            result = await handler.handle(user_query=user_query, context=ctx)

            if result.get("total", 0) == 0:
                return standard_response(
                    error_code=ErrorCodeEnum.DB_RESULT_EMPTY,
                    data="",
                    message="查询成功，但没有匹配数据",
                    trace_id=ctx.trace_id,
                    detail={"scene": normalized_scene},
                )

            return standard_response(
                error_code=ErrorCodeEnum.SUCCESS,
                data=result,
                message="查询成功",
                trace_id=ctx.trace_id,
            )
        except ProjectBaseException as exc:
            audit_log(
                operator="data_agent",
                action="error_fallback",
                input_data=normalized_scene,
                output_data=exc.error_code.value,
                success=False,
                trace_id=ctx.trace_id,
            )
            return standard_response(
                error_code=exc.error_code,
                data="",
                message=exc.message,
                trace_id=ctx.trace_id,
                detail=exc.detail,
            )
        except Exception as exc:
            audit_log(
                operator="data_agent",
                action="error_fallback",
                input_data=normalized_scene,
                output_data="unexpected_exception",
                success=False,
                trace_id=ctx.trace_id,
            )
            return standard_response(
                error_code=ErrorCodeEnum.AGENT_HANDLE_FAILED,
                data="",
                message="DataAgent 处理失败",
                trace_id=ctx.trace_id,
                detail={"error": str(exc), "scene": normalized_scene},
            )
