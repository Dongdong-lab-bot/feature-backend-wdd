"""共享的请求级 ContextVar，用于统一维护认证与租户隔离。"""
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Optional


class TenantContextMissing(RuntimeError):
    """在缺少租户上下文时访问租户相关逻辑会触发该异常。"""


user_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
tenant_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
role_var: ContextVar[Optional[str]] = ContextVar("role_type", default=None)
scope_var: ContextVar[Optional[str]] = ContextVar("scope", default=None)
app_client_var: ContextVar[Optional[str]] = ContextVar("app_client", default=None)
system_mode_var: ContextVar[bool] = ContextVar("system_mode", default=False)


@contextmanager
def system_mode_scope():
    previous = UserContext.is_system_mode()
    UserContext.set_system_mode(True)
    try:
        yield
    finally:
        UserContext.set_system_mode(previous)


class UserContext:
    """封装当前请求内依赖 ContextVar 的认证字段读写操作。"""

    @staticmethod
    def get_user_id() -> Optional[str]:
        return user_var.get()

    @staticmethod
    def set_user_id(user_id: Optional[str]) -> None:
        user_var.set(user_id)

    @staticmethod
    def require_user_id() -> str:
        user_id = user_var.get()
        if user_id is None:
            raise TenantContextMissing("缺少用户 ID，请确认认证中间件已设置。")
        return user_id

    @staticmethod
    def get_tenant_id() -> Optional[str]:
        return tenant_var.get()

    @staticmethod
    def set_tenant_id(tenant_id: Optional[str]) -> None:
        tenant_var.set(tenant_id)

    @staticmethod
    def require_tenant_id() -> str:
        tenant_id = tenant_var.get()
        if tenant_id is None:
            raise TenantContextMissing("缺少租户 ID，请确认认证中间件已设置。")
        return tenant_id

    @staticmethod
    def require_tenant_id_int() -> int:
        tenant_id = UserContext.require_tenant_id()
        try:
            return int(tenant_id)
        except ValueError as exc:
            raise TenantContextMissing("租户 ID 必须为数字。") from exc

    @staticmethod
    def get_tenant_id_int() -> Optional[int]:
        tenant_id = tenant_var.get()
        if tenant_id is None:
            return None
        try:
            return int(tenant_id)
        except ValueError:
            return None

    @staticmethod
    def get_role_type() -> Optional[str]:
        return role_var.get()

    @staticmethod
    def set_role_type(role_type: Optional[str]) -> None:
        role_var.set(role_type)

    @staticmethod
    def get_scope() -> Optional[str]:
        return scope_var.get()

    @staticmethod
    def set_scope(scope: Optional[str]) -> None:
        scope_var.set(scope)

    @staticmethod
    def get_app_client() -> Optional[str]:
        return app_client_var.get()

    @staticmethod
    def set_app_client(app_client: Optional[str]) -> None:
        app_client_var.set(app_client)

    @staticmethod
    def is_system_mode() -> bool:
        return system_mode_var.get()

    @staticmethod
    def set_system_mode(enabled: bool) -> None:
        system_mode_var.set(bool(enabled))

    @staticmethod
    def reset() -> None:
        user_var.set(None)
        tenant_var.set(None)
        role_var.set(None)
        scope_var.set(None)
        app_client_var.set(None)
        system_mode_var.set(False)

    @staticmethod
    def reset_context() -> None:
        """Backwards-compatible alias for reset()."""
        UserContext.reset()


__all__ = [
    "TenantContextMissing",
    "system_mode_scope",
    "UserContext",
    "user_var",
    "tenant_var",
    "role_var",
    "scope_var",
    "app_client_var",
    "system_mode_var",
]
