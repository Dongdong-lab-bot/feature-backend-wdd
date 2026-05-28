from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from src.core.config import jwt_settings, project_settings
from src.core.exceptions import PermissionDeniedError
from src.core.logger import log
from src.core.schemas import UserRoleEnum


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    user_role: UserRoleEnum
    claims: dict[str, Any]


def _extract_bearer_token(authorization: str) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise PermissionDeniedError(message="Authorization 缺失或格式非法")
    token = authorization[7:].strip()
    if not token:
        raise PermissionDeniedError(message="JWT Token 为空")
    return token


def _decode_verified_jwt(token: str) -> dict[str, Any]:
    try:
        import jwt as pyjwt

        payload = pyjwt.decode(
            token,
            jwt_settings.jwt_secret,
            algorithms=[jwt_settings.jwt_algorithm],
            issuer=jwt_settings.jwt_issuer,
            audience=jwt_settings.jwt_audience,
            options={"require": ["exp"], "verify_exp": True},
        )
    except Exception as exc:
        raise PermissionDeniedError(message=f"JWT 验签失败: {exc}") from exc

    if not isinstance(payload, dict):
        raise PermissionDeniedError(message="JWT payload 格式非法")
    return payload


def _decode_dev_jwt(token: str) -> dict[str, Any]:
    if project_settings.env.lower() == "prod":
        raise PermissionDeniedError(message="生产环境禁止 JWT 验签回退模式")

    log.error("JWT 验签已禁用，使用 JSON 解析 fallback（仅限开发/测试环境）")
    try:
        payload = json.loads(token)
    except json.JSONDecodeError as exc:
        raise PermissionDeniedError(message=f"JWT Token JSON 解析失败: {exc}") from exc

    if not isinstance(payload, dict):
        raise PermissionDeniedError(message="JWT Token payload 必须为 JSON 对象")
    if "exp" not in payload:
        raise PermissionDeniedError(message="JWT Token 缺少 exp 字段")
    return payload


def parse_jwt_user(authorization: str) -> AuthenticatedUser:
    token = _extract_bearer_token(authorization)

    if jwt_settings.jwt_secret and not jwt_settings.jwt_disable_verify:
        payload = _decode_verified_jwt(token)
    elif jwt_settings.jwt_disable_verify:
        payload = _decode_dev_jwt(token)
    else:
        raise PermissionDeniedError(message="JWT 验签未配置（缺少 JWT_SECRET 或 JWT_DISABLE_VERIFY）")

    user_id = str(payload.get("user_id") or "").strip()
    role_value = str(payload.get("role_type") or payload.get("user_role") or "").strip()
    if not user_id:
        raise PermissionDeniedError(message="JWT 缺少 user_id")
    try:
        user_role = UserRoleEnum(role_value)
    except Exception as exc:
        raise PermissionDeniedError(message="JWT 缺少或包含非法 role_type") from exc

    return AuthenticatedUser(user_id=user_id, user_role=user_role, claims=payload)


__all__ = ["AuthenticatedUser", "parse_jwt_user"]
