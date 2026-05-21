from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from typing import Any

from src.core.config import redis_settings
from src.core.exceptions import ConfirmationExpiredError, DBResultEmptyError, PermissionDeniedError, RouteDispatchFailedError
from src.core.logger import log
from src.core.schemas import ChatMessage, ConfirmationModel, SessionContext, UserIntentEnum, UserRoleEnum, beijing_now


def _build_redis_client() -> Any:
    try:
        import redis.asyncio as redis
    except Exception:
        return None

    return redis.Redis(
        host=redis_settings.redis_host,
        port=redis_settings.redis_port,
        password=redis_settings.redis_password,
        db=redis_settings.redis_db,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


class RouterSessionManager:
    """会话管理器：Redis 优先，失败自动降级到内存。"""

    def __init__(self, ttl_minutes: int = 30, max_history: int = 10) -> None:
        self._ttl_minutes = ttl_minutes
        self._ttl_seconds = ttl_minutes * 60
        self._max_history = max_history
        self._lock = asyncio.Lock()
        self._memory_sessions: dict[str, SessionContext] = {}
        self._memory_confirmations: dict[str, ConfirmationModel] = {}
        self._redis = _build_redis_client()
        self._redis_unavailable = self._redis is None

    def _key(self, session_id: str) -> str:
        return f"router:session:{session_id}"

    def _confirmation_key(self, confirmation_id: str) -> str:
        return f"router:confirmation:{confirmation_id}"

    async def upsert_user_message(
        self,
        *,
        session_id: str,
        user_id: str,
        user_role: UserRoleEnum,
        user_message: str,
    ) -> SessionContext:
        now = beijing_now()
        async with self._lock:
            session = await self._load_session(session_id)
            if session and session.user_id != user_id:
                raise RouteDispatchFailedError(
                    message="会话归属不一致，禁止跨用户访问",
                    detail={"session_id": session_id},
                )

            if session and session.expire_time < now:
                await self._delete_session(session_id)
                session = None

            if session is None:
                session = SessionContext(
                    session_id=session_id,
                    user_id=user_id,
                    chat_history=[],
                )

            session.updated_at = now
            session.expire_time = now + timedelta(minutes=self._ttl_minutes)
            session.chat_history.append(
                ChatMessage(role="user", content=user_message, timestamp=now)
            )
            session.chat_history = session.chat_history[-self._max_history :]

            await self._save_session(session)
            return session

    async def append_assistant_message(
        self,
        *,
        session_id: str,
        reply: str,
        intent_type: UserIntentEnum | None,
    ) -> None:
        now = beijing_now()
        async with self._lock:
            session = await self._load_session(session_id)
            if session is None:
                return

            session.updated_at = now
            session.expire_time = now + timedelta(minutes=self._ttl_minutes)
            session.chat_history.append(
                ChatMessage(
                    role="assistant",
                    content=reply,
                    timestamp=now,
                    intent_type=intent_type,
                )
            )
            session.chat_history = session.chat_history[-self._max_history :]
            await self._save_session(session)

    async def update_route_context(
        self,
        *,
        session_id: str,
        intent_type: UserIntentEnum,
        pending_confirmation_id: str | None,
        result_snapshot: dict[str, Any] | None,
    ) -> None:
        async with self._lock:
            session = await self._load_session(session_id)
            if session is None:
                return

            session.last_intent = intent_type
            session.pending_confirmation_id = pending_confirmation_id
            session.last_result_snapshot = result_snapshot
            session.updated_at = beijing_now()
            await self._save_session(session)

    async def save_confirmation(self, confirmation: ConfirmationModel) -> ConfirmationModel:
        async with self._lock:
            await self._save_confirmation(confirmation)
            return confirmation

    async def get_confirmation(self, confirmation_id: str) -> ConfirmationModel | None:
        async with self._lock:
            confirmation = await self._load_confirmation(confirmation_id)
            if confirmation is None:
                return None
            if confirmation.confirmation_status == "pending" and confirmation.expires_at < beijing_now():
                confirmation.confirmation_status = "expired"
                await self._save_confirmation(confirmation)
            return confirmation

    async def resolve_confirmation(
        self,
        *,
        confirmation_id: str,
        user_id: str,
        action: str,
        session_id: str | None = None,
    ) -> ConfirmationModel:
        if action not in {"confirm", "reject"}:
            raise RouteDispatchFailedError(
                message="确认动作非法",
                detail={"confirmation_id": confirmation_id, "action": action},
            )

        async with self._lock:
            confirmation = await self._load_confirmation(confirmation_id)
            if confirmation is None:
                raise DBResultEmptyError(message="确认单不存在", detail={"confirmation_id": confirmation_id})
            if confirmation.user_id != user_id:
                raise PermissionDeniedError(message="无权处理该确认单", detail={"confirmation_id": confirmation_id})
            if session_id is not None and confirmation.session_id != session_id:
                raise PermissionDeniedError(message="确认单与会话不匹配", detail={"confirmation_id": confirmation_id})

            if confirmation.expires_at < beijing_now():
                confirmation.confirmation_status = "expired"
                await self._save_confirmation(confirmation)
                raise ConfirmationExpiredError(message="确认单已过期", detail={"confirmation_id": confirmation_id})

            target_status = "confirmed" if action == "confirm" else "rejected"
            if confirmation.confirmation_status != "pending":
                if confirmation.confirmation_status == target_status:
                    return confirmation
                raise RouteDispatchFailedError(
                    message="确认单已处理，禁止重复变更",
                    detail={
                        "confirmation_id": confirmation_id,
                        "current_status": confirmation.confirmation_status,
                    },
                )

            confirmation.confirmation_status = target_status
            await self._save_confirmation(confirmation)
            return confirmation

    async def cleanup_expired_confirmations(self, *, session_id: str | None = None) -> int:
        """清理过期确认单，并同步回收会话挂起状态。"""
        now = beijing_now()
        async with self._lock:
            expired_ids: list[str] = []
            for confirmation_id, confirmation in list(self._memory_confirmations.items()):
                if session_id is not None and confirmation.session_id != session_id:
                    continue
                if confirmation.confirmation_status != "pending":
                    continue
                if confirmation.expires_at >= now:
                    continue
                confirmation.confirmation_status = "expired"
                await self._save_confirmation(confirmation)
                expired_ids.append(confirmation_id)

            if not expired_ids:
                return 0

            for session in list(self._memory_sessions.values()):
                if session.pending_confirmation_id not in expired_ids:
                    continue
                session.pending_confirmation_id = None
                session.updated_at = now
                await self._save_session(session)

            return len(expired_ids)

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            result: dict[str, Any] = {}
            for session_id, item in self._memory_sessions.items():
                result[session_id] = {
                    "user_id": item.user_id,
                    "chat_history_size": len(item.chat_history),
                    "expire_time": item.expire_time.isoformat(),
                }
            result["_confirmations"] = {
                confirmation_id: item.confirmation_status
                for confirmation_id, item in self._memory_confirmations.items()
            }
            return result

    async def create_session(self, *, session_id: str, user_id: str) -> SessionContext:
        now = beijing_now()
        async with self._lock:
            session = SessionContext(
                session_id=session_id,
                user_id=user_id,
                chat_history=[],
                created_at=now,
                updated_at=now,
                expire_time=now + timedelta(minutes=self._ttl_minutes),
            )
            await self._save_session(session)
            return session

    async def get_session(self, session_id: str) -> SessionContext | None:
        async with self._lock:
            session = await self._load_session(session_id)
            if session is None:
                return None
            if session.expire_time < beijing_now():
                await self._delete_session(session_id)
                return None
            return session

    async def delete_session(self, session_id: str) -> bool:
        async with self._lock:
            session = await self._load_session(session_id)
            if session is None:
                return False
            await self._delete_session(session_id)
            return True

    async def close(self) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.aclose()
        except Exception:
            pass

    async def _load_session(self, session_id: str) -> SessionContext | None:
        if not self._redis_unavailable and self._redis is not None:
            try:
                raw = await self._redis.get(self._key(session_id))
                if raw:
                    return SessionContext.model_validate(json.loads(raw))
            except Exception as exc:
                self._redis_unavailable = True
                log.warning(f"Redis 会话读取失败，降级内存模式: {exc}")

        return self._memory_sessions.get(session_id)

    async def _save_session(self, session: SessionContext) -> None:
        if not self._redis_unavailable and self._redis is not None:
            try:
                payload = json.dumps(session.model_dump(mode="json"), ensure_ascii=False)
                await self._redis.set(self._key(session.session_id), payload, ex=self._ttl_seconds)
            except Exception as exc:
                self._redis_unavailable = True
                log.warning(f"Redis 会话写入失败，降级内存模式: {exc}")

        self._memory_sessions[session.session_id] = session

    async def _load_confirmation(self, confirmation_id: str) -> ConfirmationModel | None:
        if not self._redis_unavailable and self._redis is not None:
            try:
                raw = await self._redis.get(self._confirmation_key(confirmation_id))
                if raw:
                    return ConfirmationModel.model_validate(json.loads(raw))
            except Exception as exc:
                self._redis_unavailable = True
                log.warning(f"Redis 确认单读取失败，降级内存模式: {exc}")

        return self._memory_confirmations.get(confirmation_id)

    async def _save_confirmation(self, confirmation: ConfirmationModel) -> None:
        if not self._redis_unavailable and self._redis is not None:
            try:
                payload = json.dumps(confirmation.model_dump(mode="json"), ensure_ascii=False)
                ttl_seconds = max(60, int((confirmation.expires_at - beijing_now()).total_seconds()))
                await self._redis.set(self._confirmation_key(confirmation.confirmation_id), payload, ex=ttl_seconds)
            except Exception as exc:
                self._redis_unavailable = True
                log.warning(f"Redis 确认单写入失败，降级内存模式: {exc}")

        self._memory_confirmations[confirmation.confirmation_id] = confirmation

    async def _delete_session(self, session_id: str) -> None:
        if not self._redis_unavailable and self._redis is not None:
            try:
                await self._redis.delete(self._key(session_id))
            except Exception:
                self._redis_unavailable = True
        self._memory_sessions.pop(session_id, None)


context_manager_singleton = RouterSessionManager(ttl_minutes=30, max_history=10)


__all__ = ["RouterSessionManager", "context_manager_singleton"]
